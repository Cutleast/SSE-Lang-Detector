"""
This script builds the SSE-LD.exe and packs
all its dependencies in one folder.
"""

import os
from pathlib import Path

DIST_FOLDER = Path("main.dist").resolve()
APPNAME="SSE Lang Detector"
VERSION="1.0.0"
AUTHOR="Cutleast"
LICENSE="Attribution-NonCommercial-NoDerivatives 4.0 International"
UNUSED_FILES: list[Path] = [
    DIST_FOLDER / "assets" / "config.json",
    # DIST_FOLDER / "assets" / "dictionary.json",
]

print("Building with nuitka...")
cmd = f'nuitka \
--msvc="latest" \
--standalone \
--include-data-dir="./src/assets=./assets" \
--include-data-dir="./.venv/Lib/site-packages/qtawesome=./qtawesome" \
--include-data-dir="./.venv/Lib/site-packages/lingua/language-models=./lingua/language-models" \
--enable-plugin=pyside6 \
--remove-output \
--company-name="{AUTHOR}" \
--product-name="{APPNAME}" \
--file-version="{VERSION}" \
--product-version="{VERSION}" \
--file-description="{APPNAME}" \
--copyright="{LICENSE}" \
--nofollow-import-to=tkinter \
--windows-icon-from-ico="./src/assets/icon.ico" \
--output-filename="SSE-LD.exe" \
"./src/main.py"'
os.system(cmd)

print("Deleting unused files...")
for file in UNUSED_FILES:
    if not file.is_file():
        continue
    os.remove(file)
    print(f"Removed '{file.name}'.")

print("Done!")
