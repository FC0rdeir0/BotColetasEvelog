@echo off
setlocal
cd /d "%~dp0"

title Bot de Coletas - Jadlog

echo ==========================================
echo       BOT DE COLETAS - JADLOG
echo ==========================================
echo.

rem --------------------------------------------------
rem 1. Verifica se o Python esta instalado
rem --------------------------------------------------
where python >nul 2>&1

if errorlevel 1 (
    echo ERRO: Python nao foi encontrado.
    echo.
    echo Instale o Python 3.11 ou superior.
    echo Durante a instalacao, marque:
    echo "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

rem --------------------------------------------------
rem 2. Cria o ambiente virtual na primeira execucao
rem --------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv

    if errorlevel 1 (
        echo.
        echo ERRO: Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )

    echo Ambiente virtual criado.
    echo.
)

set "PYTHON=.venv\Scripts\python.exe"

rem --------------------------------------------------
rem 3. Atualiza o pip
rem --------------------------------------------------
if not exist ".venv\.pip_instalado" (
    echo Atualizando o pip...
    "%PYTHON%" -m pip install --upgrade pip

    if errorlevel 1 (
        echo.
        echo ERRO: Nao foi possivel atualizar o pip.
        pause
        exit /b 1
    )
)

rem --------------------------------------------------
rem 4. Instala as dependencias do requirements.txt
rem --------------------------------------------------
if not exist "requirements.txt" (
    echo.
    echo ERRO: O arquivo requirements.txt nao foi encontrado.
    pause
    exit /b 1
)

if not exist ".venv\.dependencias_instaladas" (
    echo Instalando dependencias...
    "%PYTHON%" -m pip install -r requirements.txt

    if errorlevel 1 (
        echo.
        echo ERRO: Falha ao instalar as dependencias.
        pause
        exit /b 1
    )

    type nul > ".venv\.dependencias_instaladas"
    type nul > ".venv\.pip_instalado"

    echo Dependencias instaladas.
    echo.
)

rem --------------------------------------------------
rem 5. Instala o Chromium do Playwright
rem --------------------------------------------------
if not exist ".venv\.chromium_instalado" (
    echo Instalando navegador do Playwright...
    "%PYTHON%" -m playwright install chromium

    if errorlevel 1 (
        echo.
        echo ERRO: Falha ao instalar o Chromium do Playwright.
        pause
        exit /b 1
    )

    type nul > ".venv\.chromium_instalado"

    echo Chromium instalado.
    echo.
)

rem --------------------------------------------------
rem 6. Verifica se o app existe
rem --------------------------------------------------
if not exist "app.py" (
    echo.
    echo ERRO: O arquivo app.py nao foi encontrado.
    pause
    exit /b 1
)

rem --------------------------------------------------
rem 7. Cria as pastas necessarias
rem --------------------------------------------------
if not exist "dados" mkdir dados
if not exist "resultados" mkdir resultados
if not exist "perfil_jadlog" mkdir perfil_jadlog

rem --------------------------------------------------
rem 8. Inicia o aplicativo
rem --------------------------------------------------
echo Iniciando o aplicativo...
echo.
echo Para encerrar, feche esta janela ou pressione Ctrl+C.
echo.

"%PYTHON%" -m streamlit run app.py

echo.
echo Aplicativo encerrado.
pause
endlocal
