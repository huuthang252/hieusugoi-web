# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec cho Hieusugoi v2.2.1 macOS
# Build: pyinstaller Hieusugoi_mac.spec
# Yeu cau: chay tren may Mac hoac GitHub Actions macos runner

import os

# .env phai ton tai khi chay pyinstaller (tao tu GitHub Secrets hoac local)
_env_file = '.env'
_env_datas = [(_env_file, '.')] if os.path.isfile(_env_file) else []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),  # icons, images
    ] + _env_datas,            # .env duoc bundle vao sys._MEIPASS/
    hiddenimports=[
        'openai',
        'requests',
        'PyQt5',
        'pynput',
        'pynput.mouse',
        'pynput.keyboard',
        'AppKit',
        'Cocoa',
        'dotenv',
        'python_dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'ctypes.windll',
        'winreg',
        'winsound',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Hieusugoi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file='entitlements.plist',
    icon=None,  # TODO: them logo.icns
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Hieusugoi',
)

app = BUNDLE(
    coll,
    name='Hieusugoi.app',
    icon=None,
    bundle_identifier='com.hieusugoi.app',
    version='2.2.1',
    info_plist={
        'CFBundleName': 'Hieusugoi',
        'CFBundleDisplayName': 'Hieusugoi',
        'CFBundleVersion': '2.2.1',
        'CFBundleShortVersionString': '2.2.1',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
    },
)
