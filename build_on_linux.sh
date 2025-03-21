#!/bin/bash
EXTISM_DIR=$(python -c 'import os, extism_sys; print(os.path.dirname(extism_sys.__file__))')
PYGAMEEXTRA_DIR=$(python -c 'import os, pygameextra; print(os.path.dirname(pygameextra.__file__))')

python3 -m nuitka --mode=app \
--include-data-dir=assets=assets \
--include-data-dir=${PYGAMEEXTRA_DIR}/assets=pygameextra/assets \
--include-data-files=LICENSE=LICENSE \
--include-data-files=${EXTISM_DIR}/extism_sys.so=extism_sys/extism_sys.so \
--assume-yes-for-downloads --output-dir=build --script-name=moss.py --linux-icon=assets/icons/moss.png \
--deployment --disable-console
