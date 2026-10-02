@echo off
echo ========================================================
echo   Starting Chinese-to-English Translator + Public Link
echo ========================================================
echo.

REM Start Flask app in background if not already running
start /b "" .\venv2\Scripts\python.exe app.py

timeout /t 3 >nul

echo Starting public Cloudflare tunnel...
echo (Look below for your https://*.trycloudflare.com link)
echo.
.\cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
