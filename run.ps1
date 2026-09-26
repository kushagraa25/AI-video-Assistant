# AI Video & Meeting Assistant Launcher for PowerShell
Set-Location -Path $PSScriptRoot

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  🎬 AI Video & Meeting Assistant Launcher" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "[1] Run Streamlit Web Application (Browser UI)"
Write-Host "[2] Run Interactive Terminal CLI (main.py)"
Write-Host "===================================================" -ForegroundColor Cyan

$choice = Read-Host "Enter your choice (1 or 2) [default: 1]"
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

switch ($choice) {
    "1" {
        Write-Host "Starting Streamlit Web App..." -ForegroundColor Green
        python -m streamlit run frontend/app.py
    }
    "2" {
        Write-Host "Starting Terminal CLI..." -ForegroundColor Green
        python main.py
    }
    Default {
        Write-Host "Starting Streamlit Web App..." -ForegroundColor Green
        python -m streamlit run frontend/app.py
    }
}
