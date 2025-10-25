@echo off
REM SIONYX Linting Script for Windows
REM =================================

echo.
echo ========================================
echo   SIONYX Linting Script
echo ========================================
echo.

if "%1"=="install" (
    echo Installing linting dependencies...
    pip install -r requirements-dev.txt
    cd sionyx-web
    npm install
    cd ..
    echo.
    echo Dependencies installed successfully!
    goto :end
)

if "%1"=="fix" (
    echo Fixing code formatting...
    python lint.py --fix
    goto :end
)

if "%1"=="python" (
    echo Running Python linting only...
    python lint.py --python
    goto :end
)

if "%1"=="javascript" (
    echo Running JavaScript/React linting only...
    python lint.py --javascript
    goto :end
)

echo Running all linting checks...
python lint.py

:end
pause
