# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec cho Hieusugoi v2.2.1 macOS
# Build: pyinstaller Hieusugoi_mac.spec
# Yêu cầu: chạy trên máy Mac hoặc GitHub Actions macos runner

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'openai',
        'requests',
        'PyQt5',
        'pynput',
        'pynput.mouse',
        'pynput.keyboard',
        'AppKit',
        'Cocoa',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Loại trừ các module Windows-only
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
    upx=False,          # UPX thường không cần trên macOS
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,   # None = native arch; dùng 'universal2' nếu muốn fat binary
    codesign_identity=None,   # TODO: điền Developer ID khi có certificate
    entitlements_file='entitlements.plist',
    icon='assets/logo.icns',  # TODO: tạo logo.icns từ logo.ico
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

# Tạo .app bundle
app = BUNDLE(
    coll,
    name='Hieusugoi.app',
    icon='assets/logo.icns',    # TODO: tạo logo.icns
    bundle_identifier='com.hieusugoi.app',
    version='2.2.1',
    info_plist={
        'CFBundleName': 'Hieusugoi',
        'CFBundleDisplayName': 'Hieusugoi',
        'CFBundleVersion': '2.2.1',
        'CFBundleShortVersionString': '2.2.1',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,       # True = ẩn khỏi Dock (background app)
        # KHÔNG khai báo NSScreenCaptureUsageDescription — app không dùng OCR
        # Accessibility được cấp thủ công bởi user qua System Settings
    },
)
