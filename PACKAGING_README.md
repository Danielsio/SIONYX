# SIONYX Packaging Guide

This guide explains how to package your SIONYX application for distribution to end users.

## Overview

The packaging process creates:
1. **Standalone Executable** - A single .exe file with all dependencies
2. **Windows Installer** - A professional installer with setup wizard
3. **Distribution Package** - Complete package ready for distribution

## Prerequisites

Before building, ensure you have these tools installed:

### Required Tools
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **PyInstaller** - `pip install pyinstaller`
- **NSIS** - [Download](https://nsis.sourceforge.io/Download)

### Optional Tools
- **Git** - For version control
- **Visual Studio Code** - For editing

## Quick Start

### Option 1: Automated Build (Recommended)
```bash
# Full build (web + executable + installer)
build.bat

# Only create executable (fastest)
build.bat --executable-only

# Skip web build, create executable + installer
build.bat --skip-web

# Force rebuild web app even if up-to-date
build.bat --force-web
```

### Option 2: Manual Build
```bash
# 1. Build web application (only if needed)
cd sionyx-web
npm install
npm run build
cd ..

# 2. Create executable
pyinstaller sionyx.spec

# 3. Create installer (Windows only)
makensis installer.nsi
```

### Build Options

| Option | Description |
|--------|-------------|
| `--executable-only` | Only create executable, skip web build and installer |
| `--skip-web` | Skip web application build entirely |
| `--force-web` | Force rebuild of web application even if up-to-date |
| `--skip-installer` | Skip NSIS installer creation |
| `--help` | Show help message |

### Common Build Scenarios

**Fast Development Build:**
```bash
build.bat --executable-only
```

**Production Build (Full):**
```bash
build.bat
```

**Web App Updated:**
```bash
build.bat --force-web
```

**No Web Changes:**
```bash
build.bat --skip-web
```

## Build Process Details

### 1. Web Application Build
- Builds the React frontend in `sionyx-web/`
- Creates optimized production build in `sionyx-web/dist/`
- Includes all static assets and JavaScript bundles

### 2. Executable Creation
- Uses PyInstaller to create standalone executable
- Bundles all Python dependencies
- Includes web assets and templates
- Creates `dist/SIONYX.exe`

### 3. Installer Creation (Windows)
- Uses NSIS to create professional installer
- Includes setup wizard for organization configuration
- Creates desktop and start menu shortcuts
- Registers application in Add/Remove Programs
- Creates `SIONYX-Setup-1.0.0.exe`

## Configuration

### PyInstaller Configuration (`sionyx.spec`)
- **Entry Point**: `src/main.py`
- **Output Name**: `SIONYX.exe`
- **Console**: Disabled (GUI application)
- **Icon**: Uses logo from web assets
- **Data Files**: Includes templates and web assets

### NSIS Configuration (`installer.nsi`)
- **Install Directory**: `C:\Program Files\SIONYX`
- **Shortcuts**: Desktop and Start Menu
- **Uninstaller**: Included
- **Registry**: Properly registered

## First-Time Setup Wizard

When users first run SIONYX, they'll see a setup wizard that collects:

1. **Organization Details**
   - Organization ID (unique identifier)
   - Organization Name (display name)

2. **Firebase Configuration**
   - API Key
   - Auth Domain
   - Database URL
   - Project ID

3. **Payment Gateway** (Optional)
   - Nedarim Mosad ID
   - API Valid Key
   - Callback URL (pre-configured)

## Distribution Files

After building, you'll find these files in the `distribution/` folder:

- `SIONYX-Setup-1.0.0.exe` - Windows installer (recommended)
- `SIONYX.exe` - Standalone executable
- `README.txt` - Installation instructions for users

## Testing the Package

### Test the Executable
1. Copy `SIONYX.exe` to a clean Windows machine
2. Run the executable
3. Complete the setup wizard
4. Verify the application works correctly

### Test the Installer
1. Run `SIONYX-Setup-1.0.0.exe` on a clean Windows machine
2. Follow the installation wizard
3. Verify shortcuts are created
4. Test uninstallation

## Troubleshooting

### Common Issues

#### "PyInstaller not found"
```bash
pip install pyinstaller
```

#### "NSIS not found"
- Download and install NSIS from [nsis.sourceforge.io](https://nsis.sourceforge.io/)
- Add NSIS to your PATH or use full path to `makensis.exe`

#### "Node.js not found"
- Install Node.js from [nodejs.org](https://nodejs.org/)
- Ensure `npm` is available in PATH

#### "Web build failed"
- Check that all dependencies are installed: `npm install`
- Verify the web application builds: `npm run build`

#### "Executable too large"
- The executable includes all Python dependencies
- Consider using `--onefile` option in PyInstaller
- Exclude unnecessary modules in `sionyx.spec`

### Build Logs
- Check console output for detailed error messages
- PyInstaller logs are in `build/` directory
- NSIS logs show detailed installation process

## Customization

### Changing Application Icon
1. Replace `sionyx-web/public/logo.png` with your icon
2. Ensure it's a valid PNG file
3. Rebuild the application

### Modifying Installer
1. Edit `installer.nsi`
2. Change application name, version, or installation directory
3. Rebuild with `makensis installer.nsi`

### Adding Dependencies
1. Add to `requirements.txt`
2. Update `sionyx.spec` hidden imports if needed
3. Rebuild the application

## Security Considerations

- The `.env` file contains sensitive credentials
- Never commit `.env` to version control
- The installer wizard creates `.env` during first run
- Users should keep their `.env` file secure

## Deployment

### Distribution Methods
1. **Direct Download** - Host installer on your website
2. **Email Distribution** - Send installer via email
3. **USB/Physical Media** - Copy installer to USB drives
4. **Network Deployment** - Deploy via network shares

### User Instructions
Include these instructions with your distribution:

1. Download `SIONYX-Setup-1.0.0.exe`
2. Run the installer as Administrator
3. Follow the installation wizard
4. Complete the first-time setup wizard
5. Start using SIONYX!

## Support

For issues with the packaging process:
1. Check this README for common solutions
2. Review build logs for error details
3. Ensure all prerequisites are installed
4. Test on a clean Windows machine

## File Structure

```
SIONYX/
├── build.py                 # Main build script
├── build.bat               # Windows build script
├── sionyx.spec             # PyInstaller configuration
├── installer.nsi           # NSIS installer script
├── src/
│   ├── main.py            # Application entry point
│   └── ui/
│       └── installer_wizard.py  # Setup wizard
├── sionyx-web/            # React web application
├── distribution/           # Final distribution files
└── PACKAGING_README.md    # This file
```

## Version History

- **v1.0.0** - Initial packaging setup
  - PyInstaller executable creation
  - NSIS installer with setup wizard
  - Automated build process
  - First-time setup wizard
