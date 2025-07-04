setlocal

call .venv\Scripts\activate

for /f "delims=" %%i in ('python -c "import os, extism_sys; print(os.path.dirname(extism_sys.__file__))"') do set EXTISM_DIR=%%i
for /f "delims=" %%i in ('python -c "import os, rm_lines_sys; print(os.path.dirname(rm_lines_sys.__file__))"') do set LINES_DIR=%%i

for /f "delims=" %%i in ('python -c "import os, pygameextra; print(os.path.dirname(pygameextra.pygame.__file__))"') do set PYGAME_DIR=%%i
for /f "delims=" %%i in ('python -c "import os, pygameextra; print(os.path.dirname(pygameextra.__file__))"') do set PYGAMEEXTRA_DIR=%%i

python -m nuitka --mode=app --include-data-dir=assets=assets ^
--include-data-files=LICENSE=LICENSE ^
--include-data-files=%LINES_DIR%\rm_lines.dll=rm_lines_sys\rm_lines.dll ^
--include-data-files=%EXTISM_DIR%\extism_sys.so=extism_sys\extism_sys.so ^
--include-data-files=%PYGAME_DIR%\libpng16-16.dll=libpng16-16.dll ^
--include-data-dir=%PYGAMEEXTRA_DIR%\assets=pygameextra\assets ^
--assume-yes-for-downloads --output-dir=build --script-name=moss.py --windows-icon-from-ico=assets/icons/moss.ico ^
--deployment --windows-console-mode=disable --clang --nofollow-import-to=pymupdf.mupdf

endlocal