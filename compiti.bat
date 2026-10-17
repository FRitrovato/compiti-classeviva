@echo off
REM =====================================================================
REM compiti.bat  (Windows)
REM
REM Il bottone unico: doppio clic e parte. La PRIMA volta prepara Python
REM e le librerie, le volte dopo parte subito.
REM =====================================================================
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (set PY=python)
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo [!] Manca Python 3. Scaricalo da https://www.python.org/downloads/
  echo     e durante l'installazione spunta "Add python.exe to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [i] Prima volta: preparo l'ambiente Python, un minuto...
  %PY% -m venv .venv
)
".venv\Scripts\python.exe" -c "import requests, reportlab" >nul 2>nul
if errorlevel 1 (
  echo [i] Installo le librerie, requests e reportlab...
  ".venv\Scripts\python.exe" -m pip install -q --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
)

".venv\Scripts\python.exe" compiti_classeviva.py %*
echo.
pause
