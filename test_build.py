#!/usr/bin/env python3
"""
SIONYX Build Test Script
========================
This script tests the build process to ensure everything works correctly.
"""

import os
import sys
import subprocess
from pathlib import Path

def test_dependencies():
    """Test if all required dependencies are available"""
    print("Testing dependencies...")
    
    # Test Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✅ Python: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Python: {e}")
        return False
    
    # Test PyInstaller
    try:
        result = subprocess.run([sys.executable, "-m", "pyinstaller", "--version"], capture_output=True, text=True)
        print(f"✅ PyInstaller: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ PyInstaller: {e}")
        return False
    
    # Test Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print(f"✅ Node.js: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Node.js: {e}")
        return False
    
    # Test npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        print(f"✅ npm: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ npm: {e}")
        return False
    
    return True

def test_web_build():
    """Test web application build"""
    print("\nTesting web build...")
    
    web_dir = Path("sionyx-web")
    if not web_dir.exists():
        print("❌ sionyx-web directory not found")
        return False
    
    try:
        # Install dependencies
        print("Installing web dependencies...")
        result = subprocess.run(["npm", "install"], cwd=web_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            return False
        
        # Build application
        print("Building web application...")
        result = subprocess.run(["npm", "run", "build"], cwd=web_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ npm run build failed: {result.stderr}")
            return False
        
        # Check if dist directory exists
        dist_dir = web_dir / "dist"
        if not dist_dir.exists():
            print("❌ dist directory not created")
            return False
        
        print("✅ Web build successful")
        return True
        
    except Exception as e:
        print(f"❌ Web build failed: {e}")
        return False

def test_pyinstaller():
    """Test PyInstaller executable creation"""
    print("\nTesting PyInstaller...")
    
    spec_file = Path("sionyx.spec")
    if not spec_file.exists():
        print("❌ sionyx.spec not found")
        return False
    
    try:
        # Clean previous builds
        for dir_name in ["build", "dist"]:
            if Path(dir_name).exists():
                import shutil
                shutil.rmtree(dir_name)
        
        # Run PyInstaller
        print("Running PyInstaller...")
        result = subprocess.run([sys.executable, "-m", "pyinstaller", "sionyx.spec"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ PyInstaller failed: {result.stderr}")
            return False
        
        # Check if executable was created
        exe_path = Path("dist") / "SIONYX.exe"
        if not exe_path.exists():
            print("❌ Executable not created")
            return False
        
        print("✅ PyInstaller successful")
        return True
        
    except Exception as e:
        print(f"❌ PyInstaller failed: {e}")
        return False

def test_nsis():
    """Test NSIS installer creation"""
    print("\nTesting NSIS...")
    
    nsi_file = Path("installer.nsi")
    if not nsi_file.exists():
        print("❌ installer.nsi not found")
        return False
    
    try:
        # Check if NSIS is available
        result = subprocess.run(["makensis", "/VERSION"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ NSIS not found - install NSIS to test installer creation")
            return False
        
        print("✅ NSIS available")
        return True
        
    except Exception as e:
        print(f"❌ NSIS test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("SIONYX Build Test")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Web Build", test_web_build),
        ("PyInstaller", test_pyinstaller),
        ("NSIS", test_nsis)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Your build environment is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please fix the issues before building.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
