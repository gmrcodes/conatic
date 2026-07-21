# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['cliente.py'],
    pathex=[],
    binaries=[],
    datas=[('..\\resources\\logo.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[ "pytest",
    "unittest",
	"test",
    "email",
    "html",
    "pydoc",
    "doctest",
	"pandas",
	"matplotlib",
	"NumPy",
	"TensorFlow"],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    exclude_binaries=True,
    name='cliente',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['..\\resources\\icono.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='cliente',
)
