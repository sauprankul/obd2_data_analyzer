# OBD2 Data Analyzer - Build Files

This folder contains the build configuration and output for the OBD2 Data Analyzer executable.

## Building the Executable

### Quick Build
Double-click `build_exe.bat` to build the executable.

### Manual Build
```bash
cd <project_root>
pyinstaller --clean --noconfirm --distpath "run" --workpath "%TEMP%\obd2_build" run\obd2_analyzer.spec
```

## Output Structure

After building:
```
run/
  dist/
    obd2_analyzer.exe    <- Run this
    _internal/           <- Required runtime files
  obd2_analyzer.spec     <- Build configuration
  build_exe.bat          <- Build script
  pyi_rth_pyqt6_dll.py   <- Runtime hook for Qt DLLs
  logo.ico               <- Application icon
  README.md              <- This file
```

## Distribution

To distribute the application, zip the entire `run/dist/` folder. The executable requires the `_internal/` folder to be in the same directory.

## Notes

- PyQt6 is pinned to version 6.5.x due to DLL loading issues with newer versions
- The application icon is loaded from `logo.png` in the project root folder
