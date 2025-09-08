@echo off
REM Windows batch script to run py-sec-edgar examples
REM Usage:
REM   run_examples.bat                    - Interactive menu
REM   run_examples.bat --list             - List all examples
REM   run_examples.bat --run basic_processing  - Run specific example
REM   run_examples.bat --run-all          - Run all examples

echo 🎯 py-sec-edgar Examples Runner
echo ================================

REM Check if uv is available
uv --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: 'uv' command not found. Please install uv first.
    echo    Visit: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Run the Python script with all arguments
uv run python run_examples_simple.py %*

if errorlevel 1 (
    echo.
    echo ❌ Example runner failed
    pause
    exit /b 1
)

echo.
echo ✅ Example runner completed successfully
pause
