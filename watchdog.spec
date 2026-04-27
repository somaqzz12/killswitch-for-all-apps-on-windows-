# watchdog.spec
# Build with: pyinstaller watchdog.spec
# Output: dist/ProcessWatchdog.exe

block_cipher = None

a = Analysis(
    ['watchdog.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'psutil',
        'pystray', 'pystray._win32',
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
        'wmi', 'pythoncom', 'pywintypes',
        'win32api', 'win32con', 'win32gui', 'win32process',
        'customtkinter',
        'windows_toasts', 'win10toast',
        'winreg',
        'tkinter', 'tkinter.ttk', '_tkinter',
        'packaging', 'packaging.version',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib','numpy','scipy','pandas','PyQt5','PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ProcessWatchdog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',      # uncomment and add icon.ico if you have one
)
