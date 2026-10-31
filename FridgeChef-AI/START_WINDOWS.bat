@echo off
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
 echo Python was not found. Install Python and enable Add Python to PATH.
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe python -m venv .venv
if not exist .venv\Scripts\python.exe (
 echo Could not create the Python environment.
 pause
 exit /b 1
)
.venv\Scripts\python.exe -c "import flask, requests" >nul 2>&1
if errorlevel 1 (
 .venv\Scripts\python.exe -m pip install -r requirements.txt
 if errorlevel 1 (
  echo Installation failed. Check your internet connection.
  pause
  exit /b 1
 )
)
echo Open http://127.0.0.1:5000 in your browser once the server starts.
echo Keep Ollama running. Press Ctrl+C to stop.
.venv\Scripts\python.exe app.py
pause
