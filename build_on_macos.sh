#!/bin/bash
EXTISM_DIR=$(python3 -c 'import os, extism_sys; print(os.path.dirname(extism_sys.__file__))')
PYGAMEEXTRA_DIR=$(python3 -c 'import os, pygameextra; print(os.path.dirname(pygameextra.__file__))')

python3 -m nuitka --mode=app \
--include-data-dir=assets=assets \
--include-data-dir=${PYGAMEEXTRA_DIR}/assets=pygameextra/assets \
--include-data-files=LICENSE=LICENSE \
--include-data-files=${EXTISM_DIR}/libextism_sys.dylib=extism_sys/libextism_sys.dylib \
--assume-yes-for-downloads --output-dir=build --script-name=moss.py --macos-app-icon=assets/icons/moss.png \
--nofollow-import-to=pymupdf.mupdf \
--macos-app-name=Moss \
--deployment --disable-console
