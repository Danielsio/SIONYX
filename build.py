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

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


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
        print_info(
            "Copy 'build-config.example.json' to 'build-config.json' and update with your settings"
        )
        sys.exit(1)

    try:
        with open(config_file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error loading configuration: {e}")
        sys.exit(1)


def get_build_timestamp():
    """Get simple build timestamp"""
    return datetime.now().isoformat()


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
            encoding="utf-8",
            errors="replace",  # Replace problematic characters instead of failing
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
        "python": "Python 3.8+",
        "pyinstaller": "PyInstaller",
        "makensis": "NSIS (Nullsoft Scriptable Install System)",
    }

    missing_tools = []

    for tool, description in required_tools.items():
        try:
            if tool == "python":
                version = sys.version_info
                if version.major < 3 or (version.major == 3 and version.minor < 8):
                    raise Exception(
                        f"Python 3.8+ required, found {version.major}.{version.minor}"
                    )
            elif tool == "pyinstaller":
                result = run_command("pyinstaller --version", check=False)
                if result.returncode != 0:
                    raise Exception("PyInstaller not found")
            elif tool == "makensis":
                result = run_command("makensis /VERSION", check=False)
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


# Web application build removed - build separately with:
# cd sionyx-web && npm install && npm run build


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

    # Copy env.template for installer (only if it exists and is different)
    if Path("env.template").exists():
        installer_files.append(("env.template", "env.template"))

    # Skip logo for now to avoid format issues
    # installer_files.append(("sionyx-web/public/logo.png", "logo.ico"))

    for src, dst in installer_files:
        src_path = Path(src)
        if src_path.exists():
            # Skip if source and destination are the same file
            if src_path.resolve() == Path(dst).resolve():
                print_info(f"Skipping {src} -> {dst} (same file)")
                continue

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
                            print_info(
                                f"File busy, retrying in 1 second... (attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(1)
                        else:
                            print_warning(
                                f"Could not copy {src} after {max_retries} attempts: {e}"
                            )
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
            f.write(
                "Unauthorized copying, distribution, or modification is prohibited.\n"
            )

    # Run NSIS
    print_info("Running NSIS installer script...")
    run_command("makensis installer.nsi")

    # Find the created installer
    installer_path = Path("SIONYX-Installer.exe")
    if not installer_path.exists():
        print_error("Installer creation failed")
        return False

    print_success(f"Installer created: {installer_path}")
    return installer_path


# Distribution package creation removed - not needed for simple upload workflow


def upload_to_firebase_storage(
    file_path, config, build_timestamp, destination_path=None
):
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
                "sionyx-service-account.json",
            ]

            service_account_path = None
            for path in service_account_paths:
                if Path(path).exists():
                    service_account_path = path
                    break

            if not service_account_path:
                print_error("Firebase service account key not found")
                print_info(
                    "Please place your service account JSON file as 'serviceAccountKey.json'"
                )
                return False

        # Initialize Firebase Admin
        cred = credentials.Certificate(service_account_path)
        storage_bucket = config["firebase"]["storage_bucket"]

        firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})

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
            destination_path = config["build"]["upload_filename"]

        print_info(f"Uploading {file_name} ({file_size:,} bytes)")
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

        # Upload completed successfully
        return True

    except Exception as e:
        print_error(f"Upload failed: {e}")
        return False


# Removed version management - using constant filename approach


def cleanup():
    """Clean up temporary files"""
    print_header("Cleaning Up")

    temp_files = ["SIONYX.exe", "env.example", "logo.ico", "LICENSE.txt"]

    for file_name in temp_files:
        if Path(file_name).exists():
            Path(file_name).unlink()
            print_info(f"Removed {file_name}")

    print_success("Cleanup completed")


def cleanup_keep_exe():
    """Clean up temporary files but keep executable for testing"""
    print_header("Cleaning Up")

    temp_files = ["env.example", "logo.ico", "LICENSE.txt"]

    for file_name in temp_files:
        if Path(file_name).exists():
            Path(file_name).unlink()
            print_info(f"Removed {file_name}")

    print_success("Cleanup completed (kept SIONYX.exe for testing)")


def main():
    """Main build process"""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Build SIONYX installer for client distribution"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip uploading to Firebase Storage (for testing)",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config()

        print_header(f"{config['build']['app_name']} Build Process")
        print(
            f"{Colors.BOLD}Building {config['build']['app_name']} application for distribution{Colors.ENDC}\n"
        )

        # Get build timestamp
        build_timestamp = get_build_timestamp()
        print_info(f"Building on: {build_timestamp}")

        # Check dependencies
        if not check_dependencies():
            return False

        # Web application build removed - build separately
        print_info("Web application build removed - build separately with:")
        print_info("  cd sionyx-web && npm install && npm run build")

        # Create executable
        if not create_executable():
            return False

        # Create installer (always)
        installer_path = create_installer()
        if not installer_path:
            print_error("Installer creation failed")
            return False

        # Distribution package creation removed - not needed for simple upload workflow

        # Upload installer to Firebase Storage (always unless --no-upload)
        upload_success = False
        if not args.no_upload:
            upload_success = upload_to_firebase_storage(
                installer_path, config, build_timestamp
            )
            if upload_success:
                print_success("Installer uploaded to Firebase Storage")
            else:
                print_warning("Failed to upload installer")

        # Clean up local files if upload was successful
        if not args.no_upload and upload_success:
            cleanup_local_files()
        else:
            # Regular cleanup for non-upload builds - but keep executable for testing
            cleanup_keep_exe()

        print_header("Build Complete!")
        print_success(
            f"{config['build']['app_name']} has been successfully packaged for distribution"
        )
        print(f"\n{Colors.BOLD}Build Information:{Colors.ENDC}")
        print(f"  Build Time: {build_timestamp}")

        if not args.no_upload and upload_success:
            print(f"\n{Colors.BOLD}Firebase Storage:{Colors.ENDC}")
            print(f"  Files uploaded to bucket: {config['firebase']['storage_bucket']}")
            print(f"  Storage path: root level")
            print(f"  File: {config['build']['upload_filename']}")
            print(f"\n{Colors.BOLD}Local Files:{Colors.ENDC}")
            print(f"  Local files cleaned up after successful upload")
        else:
            print(f"\n{Colors.BOLD}Build files:{Colors.ENDC}")
            print(f"  {installer_path}")

        print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
        if not args.no_upload and upload_success:
            print("  1. Files are now available in Firebase Storage")
            print("  2. Users can download from your web app")
            print("  3. File is always available at the same URL")
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
