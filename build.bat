@echo off
echo 🔨 Building mdConvertor for Windows...

:: Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

:: Run PyInstaller
pyinstaller mdConvertor.spec --noconfirm

echo.
echo ✅ Build complete!
echo    Executable: dist\mdConvertor\mdConvertor.exe
echo.
