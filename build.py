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
import hashlib
import time
import re

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
    try:
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")
    except UnicodeEncodeError:
        # Fallback for systems that don't support Unicode
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")

def print_success(text):
    """Print success message"""
    try:
        print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[SUCCESS] {text}")

def print_error(text):
    """Print error message"""
    try:
        print(f"{Colors.RED}❌ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[ERROR] {text}")

def print_info(text):
    """Print info message"""
    try:
        print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[INFO] {text}")

def print_warning(text):
    """Print warning message"""
    try:
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[WARNING] {text}")

def load_config():
    """Load build configuration from file"""
    config_file = Path("build-config.json")
    if not config_file.exists():
        print_error("Configuration file 'build-config.json' not found!")
        print_info("Copy 'build-config.example.json' to 'build-config.json' and update with your settings")
        sys.exit(1)
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error loading configuration: {e}")
        sys.exit(1)

def get_next_version():
    """Get the next version number"""
    version_file = Path("version.json")
    
    if version_file.exists():
        try:
            with open(version_file, 'r') as f:
                version_data = json.load(f)
            current_version = version_data.get('version', '0.0.0')
        except:
            current_version = '0.0.0'
    else:
        current_version = '0.0.0'
    
    # Parse version (major.minor.patch)
    try:
        major, minor, patch = map(int, current_version.split('.'))
        patch += 1  # Increment patch version
        new_version = f"{major}.{minor}.{patch}"
    except:
        new_version = '1.0.0'
    
    # Save new version
    version_data = {
        'version': new_version,
        'build_date': datetime.now().isoformat(),
        'build_number': int(time.time())
    }
    
    with open(version_file, 'w') as f:
        json.dump(version_data, f, indent=2)
    
    return new_version

def cleanup_local_files():
    """Clean up local build files after successful upload"""
    print_header("Cleaning Up Local Files")
    
    # Files and directories to clean up
    cleanup_items = [
        "build",
        "dist", 
        "SIONYX.exe",
        "env.example",
        "logo.ico",
        "LICENSE.txt",
        "upload_info.json"
    ]
    
    for item in cleanup_items:
        item_path = Path(item)
        if item_path.exists():
            if item_path.is_dir():
                shutil.rmtree(item_path)
                print_info(f"Removed directory: {item}")
            else:
                item_path.unlink()
                print_info(f"Removed file: {item}")
    
    print_success("Local cleanup completed")

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
            text=True,
            encoding='utf-8',
            errors='replace'  # Replace problematic characters instead of failing
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
    
    # Add NSIS to PATH if it exists
    import os
    nsis_path = "C:\\Program Files (x86)\\NSIS"
    if os.path.exists(nsis_path):
        current_path = os.environ.get("PATH", "")
        if nsis_path not in current_path:
            os.environ["PATH"] = f"{current_path};{nsis_path}"
    
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

def build_web_app(config, force_rebuild=False):
    """Build the React web application"""
    print_header("Building Web Application")
    
    web_dir = Path(config['paths']['web_app'])
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
    
    # Build the application with proper Unicode handling
    print_info("Building web application...")
    try:
        import os
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['NODE_OPTIONS'] = '--max-old-space-size=4096'
        
        result = subprocess.run(
            "npm run build",
            shell=True,
            cwd=web_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            universal_newlines=True
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        if result.returncode != 0:
            print_error("Web build failed")
            return False
            
    except Exception as e:
        print_error(f"Web build error: {e}")
        return False
    
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
    
    # Wait a moment for file handles to be released
    import time
    time.sleep(2)
    
    # Copy necessary files for installer
    installer_files = [
        ("dist/SIONYX.exe", "SIONYX.exe"),
    ]
    
    # Copy env.example only if it's not the same file
    if Path("env.example").exists() and not Path("env.example").samefile(Path("env.example")):
        installer_files.append(("env.example", "env.example"))
    
    # Skip logo for now to avoid format issues
    # installer_files.append(("sionyx-web/public/logo.png", "logo.ico"))
    
    for src, dst in installer_files:
        src_path = Path(src)
        if src_path.exists():
            try:
                # Try to copy with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        shutil.copy2(src_path, dst)
                        print_info(f"Copied {src} -> {dst}")
                        break
                    except PermissionError as e:
                        if attempt < max_retries - 1:
                            print_info(f"File busy, retrying in 1 second... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(1)
                        else:
                            print_warning(f"Could not copy {src} after {max_retries} attempts: {e}")
                            # Try to copy without preserving metadata
                            shutil.copy(src_path, dst)
                            print_info(f"Copied {src} -> {dst} (without metadata)")
            except Exception as e:
                print_warning(f"Failed to copy {src}: {e}")
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

def upload_to_firebase_storage(file_path, config, version, destination_path=None):
    """Upload file to Firebase Storage with versioning"""
    print_header("Uploading to Firebase Storage")
    
    try:
        # Try to import Firebase Admin SDK
        try:
            import firebase_admin
            from firebase_admin import credentials, storage
        except ImportError:
            print_error("Firebase Admin SDK not installed")
            print_info("Install with: pip install firebase-admin")
            return False
        
        # Initialize Firebase Admin (if not already initialized)
        if not firebase_admin._apps:
            # Try to find service account key
            service_account_paths = [
                "serviceAccountKey.json",
                "firebase-service-account.json",
                "sionyx-service-account.json"
            ]
            
            service_account_path = None
            for path in service_account_paths:
                if Path(path).exists():
                    service_account_path = path
                    break
            
            if not service_account_path:
                print_error("Firebase service account key not found")
                print_info("Please place your service account JSON file as 'serviceAccountKey.json'")
                return False
            
        # Initialize Firebase Admin
        cred = credentials.Certificate(service_account_path)
        storage_bucket = config['firebase']['storage_bucket']
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket
        })
        
        # Get file info
        file_path = Path(file_path)
        if not file_path.exists():
            print_error(f"File not found: {file_path}")
            return False
        
        file_size = file_path.stat().st_size
        file_name = file_path.name
        
        # Generate destination path with constant filename at root level
        if not destination_path:
            # Use constant filename at bucket root for maximum simplicity
            destination_path = config['build']['upload_filename']
        
        print_info(f"Uploading {file_name} v{version} ({file_size:,} bytes)")
        print_info(f"Destination: {destination_path}")
        
        # Upload file
        bucket = storage.bucket()
        blob = bucket.blob(destination_path)
        
        # Upload file (without progress callback for compatibility)
        blob.upload_from_filename(str(file_path))
        print_info("Upload completed")
        
        # Make file publicly accessible
        blob.make_public()
        
        # Get download URL
        download_url = blob.public_url
        print_success(f"Upload completed!")
        print_info(f"Download URL: {download_url}")
        
        # Save upload info with version
        upload_info = {
            "file_name": file_name,
            "versioned_name": Path(destination_path).name,
            "version": version,
            "file_size": file_size,
            "upload_time": datetime.now().isoformat(),
            "download_url": download_url,
            "destination_path": destination_path
        }
        
        with open("upload_info.json", "w") as f:
            json.dump(upload_info, f, indent=2)
        
        # Upload version info to Firebase Storage
        upload_version_info(bucket, version, upload_info)
        
        print_success("Upload info saved to upload_info.json")
        return True
        
    except Exception as e:
        print_error(f"Upload failed: {e}")
        return False

def upload_version_info(bucket, version, upload_info):
    """Upload version information to Firebase Storage"""
    try:
        # Create version info
        version_info = {
            "version": version,
            "build_date": datetime.now().isoformat(),
            "build_number": int(time.time()),
            "files": [upload_info]
        }
        
        # Upload as latest.json
        latest_blob = bucket.blob("releases/latest.json")
        latest_blob.upload_from_string(json.dumps(version_info, indent=2))
        latest_blob.make_public()
        
        # Upload as versioned file
        version_blob = bucket.blob(f"releases/versions/v{version}.json")
        version_blob.upload_from_string(json.dumps(version_info, indent=2))
        version_blob.make_public()
        
        print_info(f"Version info uploaded: v{version}")
        
    except Exception as e:
        print_warning(f"Failed to upload version info: {e}")

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
    parser.add_argument('--upload', action='store_true',
                       help='Upload executable to Firebase Storage after building')
    parser.add_argument('--bucket', type=str, default='sionyx-19636',
                       help='Firebase Storage bucket name (default: sionyx-19636)')
    parser.add_argument('--upload-installer', action='store_true',
                       help='Also upload installer to Firebase Storage')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        print_header(f"{config['build']['app_name']} Build Process")
        print(f"{Colors.BOLD}Building {config['build']['app_name']} application for distribution{Colors.ENDC}\n")
        
        # Get version number
        version = get_next_version()
        print_info(f"Building version: {version}")
        
        # Check dependencies
        if not check_dependencies():
            return False
        
        # Build web application (unless skipped)
        if not args.skip_web and not args.executable_only:
            if not build_web_app(config, force_rebuild=args.force_web):
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
        
        # Upload to Firebase Storage if requested
        upload_success = False
        if args.upload:
            exe_path = Path("dist/SIONYX.exe")
            if exe_path.exists():
                upload_success = upload_to_firebase_storage(
                    exe_path, 
                    config,
                    version
                )
                if upload_success:
                    print_success("Executable uploaded to Firebase Storage")
                else:
                    print_warning("Failed to upload executable")
            
            if args.upload_installer and installer_path:
                upload_success = upload_to_firebase_storage(
                    installer_path, 
                    config,
                    version,
                    f"releases/{config['build']['app_name']}-Setup_v{version}.exe"
                )
                if upload_success:
                    print_success("Installer uploaded to Firebase Storage")
                else:
                    print_warning("Failed to upload installer")
        
        # Clean up local files if upload was successful
        if args.upload and upload_success:
            cleanup_local_files()
        else:
            # Regular cleanup for non-upload builds
            cleanup()
        
        print_header("Build Complete!")
        print_success(f"{config['build']['app_name']} v{version} has been successfully packaged for distribution")
        print(f"\n{Colors.BOLD}Version Information:{Colors.ENDC}")
        print(f"  Version: {version}")
        print(f"  Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if args.upload and upload_success:
            print(f"\n{Colors.BOLD}Firebase Storage:{Colors.ENDC}")
            print(f"  Files uploaded to bucket: {config['firebase']['storage_bucket']}")
            print(f"  Upload info: upload_info.json")
            print(f"  Storage path: root level")
            print(f"  File: {config['build']['upload_filename']}")
            print(f"\n{Colors.BOLD}Local Files:{Colors.ENDC}")
            print(f"  Local files cleaned up after successful upload")
        else:
            print(f"\n{Colors.BOLD}Distribution files:{Colors.ENDC}")
            print(f"  {dist_dir}")
            if installer_path:
                print(f"  {installer_path}")
        
        print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
        if args.upload and upload_success:
            print("  1. Files are now available in Firebase Storage")
            print("  2. Users can download from your web app")
            print("  3. Version info is automatically updated")
        else:
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
