#!/usr/bin/env python3
"""
SIONYX Build Script
==================
This script automates the complete build and packaging process:
1. Builds the web application
2. Creates a standalone executable with PyInstaller
3. Creates a Windows installer with NSIS
4. Packages everything for distribution
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print styled header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")

def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    print_info(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        raise

def check_dependencies():
    """Check if all required tools are installed"""
    print_header("Checking Dependencies")
    
    required_tools = {
        'python': 'Python 3.8+',
        'node': 'Node.js 16+',
        'npm': 'npm 8+',
        'pyinstaller': 'PyInstaller',
        'makensis': 'NSIS (Nullsoft Scriptable Install System)'
    }
    
    missing_tools = []
    
    for tool, description in required_tools.items():
        try:
            if tool == 'python':
                version = sys.version_info
                if version.major < 3 or (version.major == 3 and version.minor < 8):
                    raise Exception(f"Python 3.8+ required, found {version.major}.{version.minor}")
            elif tool == 'node':
                result = run_command('node --version', check=False)
                if result.returncode != 0:
                    raise Exception("Node.js not found")
            elif tool == 'npm':
                result = run_command('npm --version', check=False)
                if result.returncode != 0:
                    raise Exception("npm not found")
            elif tool == 'pyinstaller':
                result = run_command('pyinstaller --version', check=False)
                if result.returncode != 0:
                    raise Exception("PyInstaller not found")
            elif tool == 'makensis':
                result = run_command('makensis /VERSION', check=False)
                if result.returncode != 0:
                    raise Exception("NSIS not found")
            
            print_success(f"{description} - OK")
        except Exception as e:
            print_error(f"{description} - {e}")
            missing_tools.append(tool)
    
    if missing_tools:
        print_error(f"Missing required tools: {', '.join(missing_tools)}")
        print_info("Please install the missing tools and try again")
        return False
    
    return True

def build_web_app(force_rebuild=False):
    """Build the React web application"""
    print_header("Building Web Application")
    
    web_dir = Path("sionyx-web")
    if not web_dir.exists():
        print_error("sionyx-web directory not found")
        return False
    
    dist_dir = web_dir / "dist"
    
    # Check if web build already exists and is recent
    if not force_rebuild and dist_dir.exists():
        # Check if dist is newer than source files
        dist_mtime = dist_dir.stat().st_mtime
        source_files = list(web_dir.glob("src/**/*")) + list(web_dir.glob("public/**/*"))
        
        if source_files:
            latest_source = max(f.stat().st_mtime for f in source_files if f.is_file())
            if dist_mtime > latest_source:
                print_info("Web application already built and up-to-date")
                print_success("Skipping web build (use --force-web to rebuild)")
                return True
    
    # Install dependencies
    print_info("Installing web dependencies...")
    run_command("npm install", cwd=web_dir)
    
    # Build the application
    print_info("Building web application...")
    run_command("npm run build", cwd=web_dir)
    
    # Verify build output
    if not dist_dir.exists():
        print_error("Web build failed - dist directory not found")
        return False
    
    print_success("Web application built successfully")
    return True

def create_executable():
    """Create standalone executable with PyInstaller"""
    print_header("Creating Standalone Executable")
    
    # Clean previous builds
    build_dirs = ["build", "dist"]
    for dir_name in build_dirs:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print_info(f"Cleaned {dir_name}")
    
    # Run PyInstaller
    print_info("Running PyInstaller...")
    run_command("pyinstaller sionyx.spec")
    
    # Verify executable was created
    exe_path = Path("dist") / "SIONYX.exe"
    if not exe_path.exists():
        print_error("Executable creation failed")
        return False
    
    print_success(f"Executable created: {exe_path}")
    return True

def create_installer():
    """Create Windows installer with NSIS"""
    print_header("Creating Windows Installer")
    
    # Check if NSIS is available
    try:
        run_command("makensis /VERSION", check=False)
    except:
        print_error("NSIS not found. Please install NSIS to create installer")
        return False
    
    # Copy necessary files for installer
    installer_files = [
        ("dist/SIONYX.exe", "SIONYX.exe"),
        ("env.example", "env.example"),
        ("sionyx-web/public/logo.png", "logo.ico"),
    ]
    
    for src, dst in installer_files:
        src_path = Path(src)
        if src_path.exists():
            shutil.copy2(src_path, dst)
            print_info(f"Copied {src} -> {dst}")
        else:
            print_warning(f"File not found: {src}")
    
    # Create LICENSE.txt if it doesn't exist
    if not Path("LICENSE.txt").exists():
        with open("LICENSE.txt", "w") as f:
            f.write("SIONYX Software License\n")
            f.write("=" * 30 + "\n\n")
            f.write("Copyright (c) 2024 SIONYX Technologies\n\n")
            f.write("This software is proprietary and confidential.\n")
            f.write("Unauthorized copying, distribution, or modification is prohibited.\n")
    
    # Run NSIS
    print_info("Running NSIS installer script...")
    run_command("makensis installer.nsi")
    
    # Find the created installer
    installer_files = list(Path(".").glob("SIONYX-Setup-*.exe"))
    if not installer_files:
        print_error("Installer creation failed")
        return False
    
    installer_path = installer_files[0]
    print_success(f"Installer created: {installer_path}")
    return installer_path

def create_distribution_package():
    """Create a complete distribution package"""
    print_header("Creating Distribution Package")
    
    # Create distribution directory
    dist_dir = Path("distribution")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy installer
    installer_files = list(Path(".").glob("SIONYX-Setup-*.exe"))
    if installer_files:
        shutil.copy2(installer_files[0], dist_dir)
        print_info(f"Copied installer to distribution")
    
    # Copy standalone executable
    exe_path = Path("dist/SIONYX.exe")
    if exe_path.exists():
        shutil.copy2(exe_path, dist_dir)
        print_info("Copied standalone executable to distribution")
    
    # Create README for distribution
    readme_content = f"""# SIONYX Installation Package

## Files Included

- **SIONYX-Setup-{datetime.now().strftime('%Y%m%d')}.exe** - Windows installer (recommended)
- **SIONYX.exe** - Standalone executable (no installation required)

## Installation Instructions

### Option 1: Windows Installer (Recommended)
1. Run `SIONYX-Setup-{datetime.now().strftime('%Y%m%d')}.exe`
2. Follow the installation wizard
3. The installer will create shortcuts and register the application

### Option 2: Standalone Executable
1. Run `SIONYX.exe` directly
2. No installation required
3. First run will prompt for organization setup

## First-Time Setup

When you first run SIONYX, you'll need to configure:

1. **Organization ID** - Unique identifier for your organization
2. **Firebase Credentials** - Your Firebase project details
3. **Payment Gateway** - Nedarim Plus configuration (optional)

## Support

For support and documentation, visit: https://sionyx.app

## System Requirements

- Windows 10/11 (64-bit)
- 4GB RAM minimum
- 100MB free disk space
- Internet connection for Firebase connectivity

---
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(dist_dir / "README.txt", "w") as f:
        f.write(readme_content)
    
    print_success(f"Distribution package created in: {dist_dir}")
    return dist_dir

def cleanup():
    """Clean up temporary files"""
    print_header("Cleaning Up")
    
    temp_files = [
        "SIONYX.exe",
        "env.example", 
        "logo.ico",
        "LICENSE.txt"
    ]
    
    for file_name in temp_files:
        if Path(file_name).exists():
            Path(file_name).unlink()
            print_info(f"Removed {file_name}")
    
    print_success("Cleanup completed")

def main():
    """Main build process"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Build SIONYX application for distribution')
    parser.add_argument('--force-web', action='store_true', 
                       help='Force rebuild of web application even if up-to-date')
    parser.add_argument('--skip-web', action='store_true',
                       help='Skip web application build entirely')
    parser.add_argument('--skip-installer', action='store_true',
                       help='Skip NSIS installer creation')
    parser.add_argument('--executable-only', action='store_true',
                       help='Only create executable, skip web build and installer')
    
    args = parser.parse_args()
    
    try:
        print_header("🚀 SIONYX Build Process")
        print(f"{Colors.BOLD}Building SIONYX application for distribution{Colors.ENDC}\n")
        
        # Check dependencies
        if not check_dependencies():
            return False
        
        # Build web application (unless skipped)
        if not args.skip_web and not args.executable_only:
            if not build_web_app(force_rebuild=args.force_web):
                return False
        elif args.skip_web:
            print_info("Skipping web application build (--skip-web)")
        elif args.executable_only:
            print_info("Executable-only mode: skipping web build")
        
        # Create executable
        if not create_executable():
            return False
        
        # Create installer (unless skipped)
        installer_path = None
        if not args.skip_installer and not args.executable_only:
            installer_path = create_installer()
            if not installer_path:
                print_warning("Installer creation failed, but executable is available")
        elif args.skip_installer:
            print_info("Skipping installer creation (--skip-installer)")
        elif args.executable_only:
            print_info("Executable-only mode: skipping installer")
        
        # Create distribution package
        dist_dir = create_distribution_package()
        
        # Cleanup
        cleanup()
        
        print_header("🎉 Build Complete!")
        print_success("SIONYX has been successfully packaged for distribution")
        print(f"\n{Colors.BOLD}Distribution files:{Colors.ENDC}")
        print(f"  📁 {dist_dir}")
        
        if installer_path:
            print(f"  📦 {installer_path}")
        
        print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
        print("  1. Test the installer on a clean Windows machine")
        print("  2. Distribute the installer to your users")
        print("  3. Users can run the installer and follow the setup wizard")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.RED}❌ Build cancelled by user{Colors.ENDC}")
        return False
    except Exception as e:
        print_error(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
