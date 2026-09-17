@echo off
setlocal EnableExtensions EnableDelayedExpansion

title NahaLabs Reactivate

set "REPO=C:\Users\nahat\Downloads\nahalabs-content-os-github"
set "FRONTEND=%REPO%\frontend"

if not exist "%REPO%\.git" (
  echo.
  echo NahaLabs Reactivate cannot find the GitHub checkout:
  echo %REPO%
  echo.
  echo Please put this .BAT file on the same PC where the checkout exists.
  echo.
  pause
  exit /b 1
)

cd /d "%REPO%"

echo ============================================================
echo   NahaLabs Reactivate - STARTING
echo ============================================================
echo.

echo [1/5] Updating Reactivate from GitHub...
git pull --ff-only origin main
if errorlevel 1 (
  echo.
  echo Could not update from GitHub. Nothing was changed locally.
  echo.
  pause
  exit /b 1
)

echo.
echo [2/5] Freeing Reactivate ports 8000 and 5175...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /PID %%P /F >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5175" ^| findstr "LISTENING"') do taskkill /PID %%P /F >nul 2>&1

echo.
echo [3/5] Preparing backend...
python -m pip install -r "%REPO%\backend\requirements.txt"
if errorlevel 1 (
  echo.
  echo Backend dependency setup failed.
  pause
  exit /b 1
)
python -m playwright install chromium

set "REACTIVATE_CORS_ORIGINS=http://localhost:5175,http://127.0.0.1:5175,http://localhost:5173,http://127.0.0.1:5173"

echo.
echo [4/5] Starting backend on http://127.0.0.1:8000 ...
start "NahaLabs Reactivate Backend" cmd /k "cd /d %REPO% && set REACTIVATE_CORS_ORIGINS=%REACTIVATE_CORS_ORIGINS% && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

for /L %%i in (1,1,8) do (
  powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 1).StatusCode; exit 0 } catch { exit 1 }" >nul 2>&1
  if not errorlevel 1 goto BACKEND_READY
  timeout /t 1 /nobreak >nul
)

echo.
echo WARNING: Backend health did not answer yet. Continuing so its own window can show any error.

:BACKEND_READY
echo.
echo [5/5] Installing frontend dependencies if needed and starting Vite on http://localhost:5175 ...
start "NahaLabs Reactivate Frontend" cmd /k "cd /d %FRONTEND% && if not exist node_modules npm install && npm run dev -- --host localhost --port 5175"

timeout /t 5 /nobreak >nul
start "" http://localhost:5175

echo.
echo ============================================================
echo   Reactivate is launching.
echo   Backend:  http://127.0.0.1:8000/health
echo   Frontend: http://localhost:5175
echo ============================================================
echo.
exit /b 0
