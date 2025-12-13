# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OBD2 Data Analyzer

Builds a folder-based distribution (more reliable for PyQt6).
"""

import os
import sys
import shutil

# Get the project root directory
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(spec_dir)

# Add src to path for analysis
sys.path.insert(0, os.path.join(project_root, 'src'))

# Find PyQt6 installation
import PyQt6
pyqt6_path = os.path.dirname(PyQt6.__file__)
qt6_bin_path = os.path.join(pyqt6_path, 'Qt6', 'bin')
qt6_plugins_path = os.path.join(pyqt6_path, 'Qt6', 'plugins')

block_cipher = None

# Add python3.dll stub (critical for PyQt6!)
python_dir = os.path.dirname(sys.executable)
python3_dll = os.path.join(python_dir, 'python3.dll')

qt_binaries = []

# Add python3.dll if it exists
if os.path.exists(python3_dll):
    qt_binaries.append((python3_dll, '.'))

# Manually specify the Qt binaries we need
qt_dlls = [
    'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'Qt6OpenGL.dll',
    'Qt6OpenGLWidgets.dll', 'Qt6Svg.dll', 'Qt6Network.dll'
]
for dll in qt_dlls:
    dll_path = os.path.join(qt6_bin_path, dll)
    if os.path.exists(dll_path):
        qt_binaries.append((dll_path, '.'))

# Add platform plugins (critical!)
platform_plugins = os.path.join(qt6_plugins_path, 'platforms')
if os.path.exists(platform_plugins):
    for f in os.listdir(platform_plugins):
        if f.endswith('.dll'):
            qt_binaries.append((os.path.join(platform_plugins, f), 'PyQt6/Qt6/plugins/platforms'))

# Add style plugins
styles_path = os.path.join(qt6_plugins_path, 'styles')
if os.path.exists(styles_path):
    for f in os.listdir(styles_path):
        if f.endswith('.dll'):
            qt_binaries.append((os.path.join(styles_path, f), 'PyQt6/Qt6/plugins/styles'))

# Add imageformats plugins
imageformats_path = os.path.join(qt6_plugins_path, 'imageformats')
if os.path.exists(imageformats_path):
    for f in os.listdir(imageformats_path):
        if f.endswith('.dll'):
            qt_binaries.append((os.path.join(imageformats_path, f), 'PyQt6/Qt6/plugins/imageformats'))

a = Analysis(
    [os.path.join(project_root, 'src', 'obd2_native.py')],
    pathex=[
        os.path.join(project_root, 'src'),
        qt6_bin_path,
    ],
    binaries=qt_binaries,
    datas=[
        # Include loading.gif for the spinner animation
        (os.path.join(project_root, 'src', 'obd2_viewer', 'native', 'loading.gif'), 'obd2_viewer/native'),
        # Include logo.ico for taskbar icon
        (os.path.join(project_root, 'run', 'logo.ico'), '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'pyqtgraph',
        'numpy',
        'pandas',
        'scipy',
        'scipy.interpolate',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(spec_dir, 'pyi_rth_pyqt6_dll.py')],
    excludes=[
        'tkinter',
        'matplotlib', 
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'sphinx',
        'docutils',
        'psycopg2',
        'sqlalchemy',
        # Exclude PySide2/shiboken2 - they conflict with PyQt6!
        'PySide2',
        'shiboken2',
        'PySide6',
        'shiboken6',
        'PyQt5',
        'PyQt6.Qt3D',
        'PyQt6.QtBluetooth',
        'PyQt6.QtDBus',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtMultimedia',
        'PyQt6.QtNfc',
        'PyQt6.QtPositioning',
        'PyQt6.QtQuick',
        'PyQt6.QtRemoteObjects',
        'PyQt6.QtSensors',
        'PyQt6.QtSerialPort',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtWebChannel',
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebSockets',
        'PyQt6.QtXml',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Check for icon file in project root
icon_path = os.path.join(project_root, 'run', 'logo.ico')
if not os.path.exists(icon_path):
    icon_path = None

# Build as FOLDER (COLLECT) instead of single file - more reliable for Qt
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='obd2_analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='dist',  # Output to run/dist/ subfolder
)
