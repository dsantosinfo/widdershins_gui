@echo off
echo Compilando Widdershins GUI...
echo.

echo 1. Instalando dependencias...
pip install pyinstaller cx_freeze tkinterdnd2

echo.
echo 2. Compilando com PyInstaller...
pyinstaller --onefile --windowed --name "WiddershinsGUI" --add-data "node_modules;node_modules" --add-data "package.json;." widdershins_gui.py

echo.
echo 3. Executavel criado em: dist\WiddershinsGUI.exe
echo.
pause