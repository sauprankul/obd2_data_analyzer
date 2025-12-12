@echo off
echo ============================================
echo Building OBD2 Data Analyzer
echo ============================================
echo.

cd /d "%~dp0.."

:: Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Check if Pillow is installed (needed for icon conversion)
pip show pillow >nul 2>&1
if errorlevel 1 (
    echo Installing Pillow...
    pip install pillow
)

:: Always regenerate ICO from PNG to pick up any changes
echo Converting logo.png to logo.ico...
python -c "from PIL import Image; img = Image.open('logo.png'); img.save('run/logo.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)])"

echo.
echo Building executable (folder-based for reliability)...
echo.

:: Run PyInstaller with the spec file
pyinstaller --clean --noconfirm --distpath "run" --workpath "%TEMP%\obd2_build" run\obd2_analyzer.spec

echo.
if exist "run\dist\obd2_analyzer.exe" (
    echo ============================================
    echo Build successful!
    echo ============================================
    echo.
    echo Output folder: run\dist\
    echo Executable:    run\dist\obd2_analyzer.exe
    echo.
    echo To distribute: zip the entire run\dist folder
    echo.
) else (
    echo ============================================
    echo Build failed! Check the output above for errors.
    echo ============================================
)

echo.
pause
