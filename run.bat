@echo off
REM Get script directory
set "script_dir=%~dp0"

REM Remove trailing backslash (if it exists)
if "%script_dir:~-1%"=="\" set "script_dir=%script_dir:~0,-1%"

REM Get python directory
set "python_dir=%script_dir%\src\main\python"

REM Activate venv and set PYTHONPATH
call "%script_dir%\.venv\Scripts\activate"
set PYTHONPATH=%PYTHONPATH%;%python_dir%

REM Run python script
python "%python_dir%\CMOS_orchestrator\main.py"

pause