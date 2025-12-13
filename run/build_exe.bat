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
    
    :: Code signing
    echo Signing executable...
    set "CERT_FILE=run\codesign.pfx"
    if exist "%CERT_FILE%" (
        signtool sign /f "%CERT_FILE%" /p "%CODESIGN_PASSWORD%" /tr http://timestamp.digicert.com /td sha256 /fd sha256 /d "OBD2 Data Analyzer" "run\dist\obd2_analyzer.exe"
        if errorlevel 1 (
            echo WARNING: Code signing failed. Exe is unsigned.
        ) else (
            echo Code signing successful!
        )
    ) else (
        echo No certificate found at %CERT_FILE%. Skipping signing.
        echo To enable signing, place your .pfx certificate at run\codesign.pfx
        echo and set CODESIGN_PASSWORD environment variable.
    )
    
    :: Create distribution zip
    echo Creating distribution zip...
    if exist "run\obd2_analyzer.zip" del "run\obd2_analyzer.zip"
    powershell -Command "Compress-Archive -Path 'run\dist\*' -DestinationPath 'run\obd2_analyzer.zip' -Force"
    if exist "run\obd2_analyzer.zip" (
        echo Distribution zip created: run\obd2_analyzer.zip
    ) else (
        echo WARNING: Failed to create distribution zip.
    )
    
    echo.
    echo Output folder: run\dist\
    echo Executable:    run\dist\obd2_analyzer.exe
    echo Distribution:  run\obd2_analyzer.zip
    echo.
) else (
    echo ============================================
    echo Build failed! Check the output above for errors.
    echo ============================================
)

echo.
pause
