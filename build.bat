python build.py --upload
@echo off
echo SIONYX Build Script
echo ===================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Show usage if help requested
if "%1"=="--help" (
    echo Usage: build.bat [options]
    echo.
    echo Options:
    echo   --executable-only    Only create executable, skip web build and installer
    echo   --skip-web          Skip web application build
    echo   --force-web         Force rebuild of web application
    echo   --skip-installer    Skip NSIS installer creation
    echo   --upload            Upload executable to Firebase Storage
    echo   --upload-installer  Also upload installer to Firebase Storage
    echo   --bucket NAME       Firebase Storage bucket name (default: sionyx-19636)
    echo   --help              Show this help message
    echo.
    echo Examples:
    echo   build.bat                           # Full build (web + executable + installer)
    echo   build.bat --executable-only         # Only create executable
    echo   build.bat --skip-web                # Skip web build, create executable + installer
    echo   build.bat --upload                  # Build, upload to Firebase, clean local files
    echo   build.bat --upload --upload-installer # Build, upload both files, clean local files
    echo.
    echo Setup Firebase Storage:
    echo   python setup_firebase.py            # Interactive Firebase setup
    echo.
    pause
    exit /b 0
)

REM Show usage if no arguments provided
if "%1"=="" (
    echo Usage: build.bat [options]
    echo.
    echo Options:
    echo   --executable-only    Only create executable, skip web build and installer
    echo   --skip-web          Skip web application build
    echo   --force-web         Force rebuild of web application
    echo   --skip-installer    Skip NSIS installer creation
    echo   --upload            Upload executable to Firebase Storage
    echo   --upload-installer  Also upload installer to Firebase Storage
    echo   --bucket NAME       Firebase Storage bucket name (default: sionyx-19636)
    echo   --help              Show this help message
    echo.
    echo Examples:
    echo   build.bat                           # Full build (web + executable + installer)
    echo   build.bat --executable-only         # Only create executable
    echo   build.bat --skip-web                # Skip web build, create executable + installer
    echo   build.bat --upload                  # Build, upload to Firebase, clean local files
    echo   build.bat --upload --upload-installer # Build, upload both files, clean local files
    echo.
    echo Setup Firebase Storage:
    echo   python setup_firebase.py            # Interactive Firebase setup
    echo.
    pause
    exit /b 0
)

REM Run the build script with all arguments
echo Running build process...
python build.py %*

if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Check the 'distribution' folder for your installer.
echo.
pause
