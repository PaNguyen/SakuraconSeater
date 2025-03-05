# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['sakuraconseater.py'],
    pathex=["mysettings", "mysettings.py"],
    binaries=[],
    datas=[("templates", "templates"),
           ("static", "static"),
           # ("static/css/*", "static/css"),
           # ("static/fonts/*", "static/fonts"),
           # ("static/js/*", "static/js"),
           # ("static/mustache/*", "static/mustache"),
           ("sakuraconseater.bat", ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["mysettings", "mysettings.py"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sakuraconseater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    upx=True,
    upx_exclude=[],
    name='sakuraconseater',
)
