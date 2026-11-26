#!/usr/bin/env python3
"""Step 8: build the four upload archives for Zenodo from zenodo/*.json.

Plain-language summary: makes one zip per Zenodo record (library, benchmark,
moisture extension, software) in release/, containing exactly the files that
record's metadata lists. Run after verification and after the --final rebuild.
"""

import glob
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    os.makedirs(os.path.join(ROOT, "release"), exist_ok=True)
    for meta_path in sorted(glob.glob(os.path.join(ROOT, "zenodo", "*.json"))):
        name = os.path.splitext(os.path.basename(meta_path))[0]
        spec = json.load(open(meta_path))
        version = spec["metadata"]["version"]
        out = os.path.join(ROOT, "release", f"greensand-nir-{name}-v{version}.zip")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for item in spec["files"]:
                p = os.path.join(ROOT, item)
                if not os.path.exists(p):
                    raise SystemExit(f"{meta_path}: listed file or folder is missing: {item}")
                paths = [p] if os.path.isfile(p) else sorted(
                    q for q in glob.glob(os.path.join(p, "**", "*"), recursive=True)
                    if os.path.isfile(q) and "__pycache__" not in q and ".egg-info" not in q)
                for q in paths:
                    # fixed timestamp so the same files always give the same archive
                    info = zipfile.ZipInfo(os.path.join(f"greensand-nir-{name}-v{version}", os.path.relpath(q, ROOT)),
                                           date_time=(2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    with open(q, "rb") as fh:
                        z.writestr(info, fh.read())
        print(f"{out}  {os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
