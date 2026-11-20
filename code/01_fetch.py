#!/usr/bin/env python3
"""Step 1: download every raw input and log where it came from.

Plain-language summary: this script downloads the public USGS spectra and the
public water data this project is built on, then writes a line for each file in
data/raw/PROVENANCE.txt (file name, size, a fingerprint called SHA-256, the
link, and the date). You do not need to open this file; just run it.

Inputs (all public domain):
  - USGS Spectral Library Version 7, ASCII data convolved to ASD resolution
    (Kokaly et al. 2017, https://doi.org/10.5066/F7RR1WDJ), ScienceBase item
    586e8c88e4b0f5ce109fccae.
  - Liquid water optical constants, Segelstein (1981), via the
    refractiveindex.info database (CC0).

Only the spectra named in config/mixing_rules.json (plus validation spectra)
are extracted into data/raw/splib07_selected/; the full archive stays in
data/raw/cache/ and is not committed.
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
CACHE = os.path.join(RAW, "cache")
SEL = os.path.join(RAW, "splib07_selected")
PROV = os.path.join(RAW, "PROVENANCE.txt")

SPLIB_URL = ("https://www.sciencebase.gov/catalog/file/get/586e8c88e4b0f5ce109fccae"
             "?f=__disk__6f%2F81%2F62%2F6f8162500e6f3d250883a27b3def74cb77b927fc")
SPLIB_ZIP = "ASCIIdata_splib07b_cvASD.zip"
SPLIB_SHA = None  # filled from PROVENANCE.txt on first run; checked on later runs
WATER_URL = ("https://raw.githubusercontent.com/polyanskiy/refractiveindex.info-database/"
             "master/database/data/main/H2O/nk/Segelstein.yml")
WATER_FILE = "water_nk_Segelstein1981.yml"
HOW_FOUND = ("ScienceBase JSON listing: https://www.sciencebase.gov/catalog/item/"
             "586e8c88e4b0f5ce109fccae?format=json, file ASCIIdata_splib07b_cvASD.zip")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, dest, note=""):
    if not os.path.exists(dest):
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, dest)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "provenance.py"), dest, url,
                    "--log", PROV, "--note", note], check=True)


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(SEL, exist_ok=True)
    if os.path.exists(PROV):
        os.remove(PROV)  # rewritten on every run so it reflects this fetch
    zpath = os.path.join(CACHE, SPLIB_ZIP)
    fetch(SPLIB_URL, zpath, HOW_FOUND)
    fetch(WATER_URL, os.path.join(SEL, WATER_FILE), "refractiveindex.info database, CC0")

    with open(os.path.join(ROOT, "config", "mixing_rules.json")) as f:
        rules = json.load(f)
    wanted = {rules["wavelength_file"], rules["bandpass_file"]}
    for comp in rules["components"].values():
        wanted.add(comp["spectrum"])
        for alt in comp.get("alternatives", {}).values():
            wanted.add(alt)
    for v in rules["validation_spectra"].values():
        wanted.add(v)

    with zipfile.ZipFile(zpath) as z:
        names = {os.path.basename(n): n for n in z.namelist()}
        missing = sorted(w for w in wanted if w not in names)
        if missing:
            sys.exit(f"Not found in archive: {missing}")
        for w in sorted(wanted):
            out = os.path.join(SEL, w)
            with z.open(names[w]) as src, open(out, "wb") as dst:
                dst.write(src.read())
            with open(PROV, "a") as log:
                log.write(f"  extracted {w} | sha256:{sha256(out)} | from {names[w]}\n")
    print(f"extracted {len(wanted)} files to {os.path.relpath(SEL, ROOT)}")


if __name__ == "__main__":
    main()
