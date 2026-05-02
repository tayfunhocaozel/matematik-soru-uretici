@echo off
title Soru Agent
echo Soru Agent basliyor...
echo Tarayicinizda: http://localhost:5000
echo Durdurmak icin: CTRL+C
echo.
call "%USERPROFILE%\.notebooklm-venv\Scripts\activate.bat"
python "%~dp0app.py"
pause
