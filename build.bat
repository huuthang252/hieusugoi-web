@echo off
REM Build script for Hieusugoi v2.1.0 (Clipboard Copy mode)
REM Run this in the project root containing:
REM - main.py
REM - Hieusugoi.spec

py -m pip install --upgrade pip
py -m pip install pyinstaller PyQt5 openai requests

py -m PyInstaller --clean --noconfirm Hieusugoi.spec

echo.
echo Build finished. Check dist\Hieusugoi\Hieusugoi.exe
pause
