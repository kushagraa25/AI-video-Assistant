@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo   🎬 AI Video & Meeting Assistant Launcher
echo ===================================================
echo [1] Run Streamlit Web Application (Browser UI)
echo [2] Run Interactive Terminal CLI (main.py)
echo ===================================================
set /p choice="Enter your choice (1 or 2) [default: 1]: "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo Starting Streamlit Web App...
    python -m streamlit run frontend/app.py
) else if "%choice%"=="2" (
    echo Starting Terminal CLI...
    python main.py
) else (
    echo Starting Streamlit Web App...
    python -m streamlit run frontend/app.py
)

pause
