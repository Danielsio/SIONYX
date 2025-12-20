#!/usr/bin/env python3
"""
SIONYX Build Script with Semantic Versioning
=============================================
Build and release SIONYX with proper version management.

Usage:
    python build.py                    # Increment patch (1.0.0 -> 1.0.1)
    python build.py --minor            # Increment minor (1.0.1 -> 1.1.0)
    python build.py --major            # Increment major (1.1.0 -> 2.0.0)
    python build.py --no-upload        # Build only, don't upload
    python build.py --version 1.2.3    # Set specific version
    python build.py --dry-run          # Show what would happen
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
from typing import Optional, Tuple


# =============================================================================
# STYLING
# =============================================================================

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
    try:
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")
    except UnicodeEncodeError:
        print(f"\n{'='*70}\n  {text}\n{'='*70}\n")


def print_success(text):
    try:
        print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[SUCCESS] {text}")


def print_error(text):
    try:
        print(f"{Colors.RED}❌ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[ERROR] {text}")


def print_info(text):
    try:
        print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[INFO] {text}")


def print_warning(text):
    try:
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"[WARNING] {text}")


# =============================================================================
# VERSION MANAGEMENT
# =============================================================================

VERSION_FILE = Path("version.json")


def load_version() -> dict:
    """Load version information from version.json"""
    if not VERSION_FILE.exists():
        # Create default version file
        default_version = {
            "version": "1.0.0",
            "major": 1,
            "minor": 0,
            "patch": 0,
            "buildNumber": 0,
            "lastBuildDate": None,
            "changelog": []
        }
        save_version(default_version)
        return default_version
    
    with open(VERSION_FILE, "r") as f:
        return json.load(f)


def save_version(version_data: dict):
    """Save version information to version.json"""
    with open(VERSION_FILE, "w") as f:
        json.dump(version_data, f, indent=2)


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string into (major, minor, patch)"""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def increment_version(
    current: dict,
    increment_type: str = "patch",
    specific_version: Optional[str] = None
) -> dict:
    """
    Increment version based on type.
    
    Rules (following semantic versioning):
    - patch: x.y.z -> x.y.(z+1)
    - minor: x.y.z -> x.(y+1).0  (resets patch)
    - major: x.y.z -> (x+1).0.0  (resets minor and patch)
    """
    if specific_version:
        major, minor, patch = parse_version(specific_version)
    else:
        major = current.get("major", 1)
        minor = current.get("minor", 0)
        patch = current.get("patch", 0)
        
        if increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif increment_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
    
    current["major"] = major
    current["minor"] = minor
    current["patch"] = patch
    current["version"] = f"{major}.{minor}.{patch}"
    current["buildNumber"] = current.get("buildNumber", 0) + 1
    current["lastBuildDate"] = datetime.now().isoformat()
    
    return current


def get_installer_filename(version: str) -> str:
    """Generate installer filename with version"""
    return f"sionyx-installer-v{version}.exe"


def get_version_display(version_data: dict) -> str:
    """Get formatted version for display"""
    return f"v{version_data['version']} (build #{version_data.get('buildNumber', 1)})"


# =============================================================================
# CONFIGURATION
# =============================================================================

def load_config() -> dict:
    """Load build configuration"""
    config_file = Path("build-config.json")
    if not config_file.exists():
        print_error("Configuration file 'build-config.json' not found!")
        sys.exit(1)
    
    with open(config_file, "r") as f:
        return json.load(f)


def run_command(command, cwd=None, check=True):
    """Run a shell command"""
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
            errors="replace",
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stderr:
            print(e.stderr)
        raise


# =============================================================================
# BUILD STEPS
# =============================================================================

def check_dependencies() -> bool:
    """Check required tools"""
    print_header("Checking Dependencies")
    
    nsis_path = "C:\\Program Files (x86)\\NSIS"
    if os.path.exists(nsis_path):
        os.environ["PATH"] = f"{os.environ.get('PATH', '')};{nsis_path}"
    
    tools = {
        "python": "Python 3.8+",
        "pyinstaller": "PyInstaller",
        "makensis": "NSIS",
    }
    
    all_ok = True
    for tool, desc in tools.items():
        try:
            if tool == "python":
                if sys.version_info < (3, 8):
                    raise Exception("Python 3.8+ required")
            elif tool == "pyinstaller":
                if run_command("pyinstaller --version", check=False).returncode != 0:
                    raise Exception("Not found")
            elif tool == "makensis":
                if run_command("makensis /VERSION", check=False).returncode != 0:
                    raise Exception("Not found")
            print_success(f"{desc} - OK")
        except Exception as e:
            print_error(f"{desc} - {e}")
            all_ok = False
    
    return all_ok


def create_executable() -> bool:
    """Create standalone executable"""
    print_header("Creating Executable")
    
    for d in ["build", "dist"]:
        if Path(d).exists():
            shutil.rmtree(d)
    
    run_command("pyinstaller sionyx.spec")
    
    if not Path("dist/SIONYX.exe").exists():
        print_error("Executable creation failed")
        return False
    
    print_success("Executable created")
    return True


def create_installer(version: str) -> Optional[Path]:
    """Create Windows installer with version in filename"""
    print_header(f"Creating Installer v{version}")
    
    time.sleep(2)  # Wait for file handles
    
    # Copy files
    if Path("dist/SIONYX.exe").exists():
        shutil.copy2("dist/SIONYX.exe", "SIONYX.exe")
    
    # env.template is already in place for the installer
    
    # Create LICENSE
    if not Path("LICENSE.txt").exists():
        with open("LICENSE.txt", "w") as f:
            f.write(f"SIONYX Software License\nVersion {version}\n")
            f.write("Copyright (c) 2024 SIONYX Technologies\n")
    
    # Run NSIS
    run_command("makensis installer.nsi")
    
    # Rename with version
    old_name = Path("SIONYX-Installer.exe")
    new_name = Path(get_installer_filename(version))
    
    if old_name.exists():
        if new_name.exists():
            new_name.unlink()
        old_name.rename(new_name)
        print_success(f"Installer created: {new_name}")
        return new_name
    
    print_error("Installer creation failed")
    return None


# =============================================================================
# FIREBASE STORAGE
# =============================================================================

def delete_old_versions(bucket, current_version: str, prefix: str = "releases/"):
    """Delete old installer versions from Firebase Storage"""
    print_info("Cleaning up old versions...")
    
    blobs = list(bucket.list_blobs(prefix=prefix))
    current_filename = get_installer_filename(current_version)
    
    deleted_count = 0
    for blob in blobs:
        # Keep metadata file and current version
        if blob.name.endswith(".json"):
            continue
        if blob.name.endswith(current_filename):
            continue
        
        # Delete old installers
        if "sionyx-installer" in blob.name.lower() and blob.name.endswith(".exe"):
            print_info(f"Deleting old version: {blob.name}")
            blob.delete()
            deleted_count += 1
    
    if deleted_count > 0:
        print_success(f"Deleted {deleted_count} old version(s)")
    else:
        print_info("No old versions to clean up")


def upload_to_firebase(installer_path: Path, version_data: dict, config: dict) -> bool:
    """Upload installer and version metadata to Firebase Storage"""
    print_header("Uploading to Firebase Storage")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, storage
    except ImportError:
        print_error("firebase-admin not installed. Run: pip install firebase-admin")
        return False
    
    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred, {
                "storageBucket": config["firebase"]["storage_bucket"]
            })
        
        bucket = storage.bucket()
        version = version_data["version"]
        
        # Delete old versions first
        delete_old_versions(bucket, version, "releases/")
        
        # Upload installer
        installer_filename = get_installer_filename(version)
        installer_blob_path = f"releases/{installer_filename}"
        
        print_info(f"Uploading {installer_path} -> {installer_blob_path}")
        
        blob = bucket.blob(installer_blob_path)
        blob.upload_from_filename(str(installer_path))
        blob.make_public()
        
        installer_url = blob.public_url
        print_success(f"Installer uploaded: {installer_url}")
        
        # Also upload to constant path for backwards compatibility
        latest_blob = bucket.blob("sionyx-installer.exe")
        latest_blob.upload_from_filename(str(installer_path))
        latest_blob.make_public()
        print_info(f"Also uploaded as: sionyx-installer.exe (backwards compat)")
        
        # Upload version metadata
        metadata = {
            "version": version,
            "major": version_data["major"],
            "minor": version_data["minor"],
            "patch": version_data["patch"],
            "buildNumber": version_data["buildNumber"],
            "releaseDate": datetime.now().isoformat(),
            "downloadUrl": installer_url,
            "filename": installer_filename,
            "changelog": version_data.get("changelog", [])
        }
        
        metadata_blob = bucket.blob("releases/latest.json")
        # Set no-cache headers to prevent stale version info
        metadata_blob.cache_control = "no-cache, no-store, must-revalidate"
        metadata_blob.upload_from_string(
            json.dumps(metadata, indent=2),
            content_type="application/json"
        )
        metadata_blob.make_public()
        print_success(f"Version metadata uploaded: {metadata_blob.public_url}")
        
        return True
        
    except Exception as e:
        print_error(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# CLEANUP
# =============================================================================

def cleanup_local_files(keep_installer: bool = False):
    """Clean up local build artifacts"""
    print_header("Cleaning Up")
    
    items_to_remove = ["build", "dist", "SIONYX.exe", "LICENSE.txt"]
    
    if not keep_installer:
        # Remove versioned installers
        for f in Path(".").glob("sionyx-installer-*.exe"):
            f.unlink()
            print_info(f"Removed {f}")
    
    for item in items_to_remove:
        p = Path(item)
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            print_info(f"Removed {item}")
    
    print_success("Cleanup completed")


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build SIONYX with semantic versioning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                Build with patch increment (1.0.0 -> 1.0.1)
  python build.py --minor        Build with minor increment (1.0.1 -> 1.1.0)
  python build.py --major        Build with major increment (1.1.0 -> 2.0.0)
  python build.py --version 2.0.0  Build with specific version
  python build.py --dry-run      Show version changes without building
        """
    )
    
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument("--major", action="store_true", help="Increment major version (x.0.0)")
    version_group.add_argument("--minor", action="store_true", help="Increment minor version (x.y.0)")
    version_group.add_argument("--patch", action="store_true", help="Increment patch version (default)")
    version_group.add_argument("--version", type=str, help="Set specific version (e.g., 2.0.0)")
    
    parser.add_argument("--no-upload", action="store_true", help="Skip upload to Firebase")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--keep-local", action="store_true", help="Keep local installer after upload")
    
    args = parser.parse_args()
    
    try:
        # Load config and version
        config = load_config()
        version_data = load_version()
        
        current_version = version_data["version"]
        
        # Determine increment type
        if args.major:
            increment_type = "major"
        elif args.minor:
            increment_type = "minor"
        else:
            increment_type = "patch"
        
        # Calculate new version
        new_version_data = increment_version(
            version_data.copy(),
            increment_type,
            args.version
        )
        new_version = new_version_data["version"]
        
        print_header(f"SIONYX Build System")
        print(f"  Current version: v{current_version}")
        print(f"  New version:     v{new_version} ({increment_type} increment)")
        print(f"  Build number:    #{new_version_data['buildNumber']}")
        print(f"  Output file:     {get_installer_filename(new_version)}")
        print()
        
        if args.dry_run:
            print_warning("DRY RUN - No changes will be made")
            return True
        
        # Check dependencies
        if not check_dependencies():
            return False
        
        # Create executable
        if not create_executable():
            return False
        
        # Create installer
        installer_path = create_installer(new_version)
        if not installer_path:
            return False
        
        # Save version file
        save_version(new_version_data)
        print_success(f"Version updated to v{new_version}")
        
        # Upload to Firebase
        upload_success = False
        if not args.no_upload:
            upload_success = upload_to_firebase(installer_path, new_version_data, config)
        
        # Cleanup
        if upload_success:
            cleanup_local_files(keep_installer=args.keep_local)
        else:
            cleanup_local_files(keep_installer=True)
        
        # Summary
        print_header("Build Complete!")
        print(f"  Version:    v{new_version}")
        print(f"  Build:      #{new_version_data['buildNumber']}")
        print(f"  Installer:  {get_installer_filename(new_version)}")
        
        if upload_success:
            print_success("Uploaded to Firebase Storage")
            print_success("Old versions cleaned up")
            print_success("Version metadata updated")
        elif not args.no_upload:
            print_warning("Upload failed - installer kept locally")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Build cancelled{Colors.ENDC}")
        return False
    except Exception as e:
        print_error(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
