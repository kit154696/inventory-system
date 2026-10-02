@echo off
setlocal

echo ============================================
echo   StockApp - Build Script (Windows)
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Install Python 3.11+ from python.org and retry.
    exit /b 1
)

echo.
echo [1/4] Installing runtime dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [2/4] Installing PyInstaller (build-time only)...
python -m pip install pyinstaller==6.10.0
if errorlevel 1 goto :fail

echo.
echo [3/4] Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [4/4] Building StockApp.exe (one-folder mode)...
pyinstaller --noconfirm --windowed --name StockApp ^
    --add-data "assets;assets" ^
    main.py
if errorlevel 1 goto :fail

echo.
echo ============================================
echo   Build complete!
echo   Output: dist\StockApp\StockApp.exe
echo ============================================
exit /b 0

:fail
echo.
echo [ERROR] Build failed. See output above for details.
exit /b 1
