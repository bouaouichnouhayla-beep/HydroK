# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files


datas = [
    ("assets", "assets"),
]
datas += collect_data_files("matplotlib")
datas += collect_data_files("certifi")

hiddenimports = [
    "tkintermapview",
    "requests",
    "certifi",
    "PIL._tkinter_finder",
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_tkagg",
    "reportlab.pdfbase._fontdata",
    "reportlab.pdfbase.ttfonts",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={
        "matplotlib": {
            "backends": ["TkAgg", "Agg"],
        },
    },
    runtime_hooks=[],
    excludes=["tests", "pytest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="HydroK",
    icon="assets/icone_hydrok.ico",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="HydroK",
)
