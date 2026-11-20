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
                paths = [p] if os.path.isfile(p) else [q for q in glob.glob(os.path.join(p, "**", "*"), recursive=True)
                                                        if os.path.isfile(q) and "__pycache__" not in q]
                for q in paths:
                    z.write(q, os.path.join(f"greensand-nir-{name}-v{version}", os.path.relpath(q, ROOT)))
        print(f"{out}  {os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
