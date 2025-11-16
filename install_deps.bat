@echo off
echo Instalando dependencias do Widdershins GUI...
echo.

echo Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js nao encontrado!
    echo Baixe e instale de: https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Node.js encontrado
echo.

echo Verificando npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm nao encontrado!
    pause
    exit /b 1
)

echo ✅ npm encontrado
echo.

echo 📦 Instalando Widdershins...
npm install

if %errorlevel% equ 0 (
    echo.
    echo ✅ Instalacao concluida com sucesso!
    echo ✅ Agora voce pode executar: python widdershins_gui.py
) else (
    echo.
    echo ❌ Erro na instalacao
)

echo.
pause