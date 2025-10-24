#!/usr/bin/env python3
"""
Firebase Setup Helper for SIONYX
================================
This script helps you set up Firebase Storage for automatic uploads.
"""

import os
import sys
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def setup_firebase_storage():
    """Guide user through Firebase Storage setup"""
    print_header("Firebase Storage Setup for SIONYX")
    
    print("This script will help you set up Firebase Storage for automatic uploads.")
    print("You'll need your Firebase project credentials.\n")
    
    # Check if service account already exists
    service_account_paths = [
        "serviceAccountKey.json",
        "firebase-service-account.json", 
        "sionyx-service-account.json"
    ]
    
    existing_key = None
    for path in service_account_paths:
        if Path(path).exists():
            existing_key = path
            break
    
    if existing_key:
        print_success(f"Found existing service account: {existing_key}")
        use_existing = input("Use existing service account? (y/n): ").lower().strip()
        if use_existing in ['y', 'yes']:
            return True
    
    print("\nTo get your Firebase service account key:")
    print("1. Go to https://console.firebase.google.com/")
    print("2. Select your project (sionyx-19636)")
    print("3. Go to Project Settings → Service Accounts")
    print("4. Click 'Generate new private key'")
    print("5. Download the JSON file")
    print("6. Save it as 'serviceAccountKey.json' in this directory")
    
    input("\nPress Enter when you have the service account key file...")
    
    # Check if file was created
    if not Path("serviceAccountKey.json").exists():
        print_error("serviceAccountKey.json not found!")
        print("Please download the service account key and save it as 'serviceAccountKey.json'")
        return False
    
    # Validate the JSON file
    try:
        with open("serviceAccountKey.json", 'r') as f:
            key_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in key_data]
        
        if missing_fields:
            print_error(f"Invalid service account key. Missing fields: {missing_fields}")
            return False
        
        print_success("Service account key is valid!")
        print_info(f"Project ID: {key_data.get('project_id')}")
        print_info(f"Client Email: {key_data.get('client_email')}")
        
        return True
        
    except json.JSONDecodeError:
        print_error("Invalid JSON file!")
        return False
    except Exception as e:
        print_error(f"Error reading service account key: {e}")
        return False

def test_firebase_connection():
    """Test Firebase Storage connection"""
    print_header("Testing Firebase Connection")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, storage
    except ImportError:
        print_error("Firebase Admin SDK not installed!")
        print("Install with: pip install firebase-admin")
        return False
    
    try:
        # Initialize Firebase Admin
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'sionyx-19636.appspot.com'
        })
        
        # Test connection
        bucket = storage.bucket()
        print_success("Firebase connection successful!")
        print_info(f"Bucket: {bucket.name}")
        
        return True
        
    except Exception as e:
        print_error(f"Firebase connection failed: {e}")
        return False

def setup_storage_rules():
    """Guide user through setting up Storage rules"""
    print_header("Firebase Storage Rules Setup")
    
    print("Your Firebase Storage uses Firestore-based authentication rules.")
    print("You need to update the rules to allow public read access for releases.")
    print("\n1. Go to https://console.firebase.google.com/")
    print("2. Select your project (sionyx-19636)")
    print("3. Go to Storage → Rules")
    print("4. Update the rules to include public read access for releases:")
    
    rules = '''rules_version = '2';

// Craft rules based on data in your Firestore database
// allow write: if firestore.get(
//    /databases/(default)/documents/users/$(request.auth.uid)).data.isAdmin;
service firebase.storage {
  match /b/{bucket}/o {
    // Public read access for releases (for SIONYX downloads)
    match /releases/{allPaths=**} {
      allow read: if true;
      allow write: if false; // Only admin can write via service account
    }
    
    // Keep existing rules for other paths
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}'''
    
    print(f"\n{'-'*60}")
    print(rules)
    print(f"{'-'*60}")
    
    print("\n5. Click 'Publish'")
    print("\nNote: This allows public read access only for the 'releases/' folder")
    print("while keeping your existing authentication rules for other paths.")
    input("\nPress Enter when you have updated the Storage rules...")
    
    return True

def main():
    """Main setup process"""
    print_header("SIONYX Firebase Storage Setup")
    
    # Step 1: Setup service account
    if not setup_firebase_storage():
        print_error("Setup failed at service account step")
        return False
    
    # Step 2: Test connection
    if not test_firebase_connection():
        print_error("Setup failed at connection test")
        return False
    
    # Step 3: Setup storage rules
    if not setup_storage_rules():
        print_error("Setup failed at storage rules step")
        return False
    
    print_header("🎉 Setup Complete!")
    print_success("Firebase Storage is now configured for SIONYX")
    print("\nYou can now run:")
    print("  build.bat --upload")
    print("\nThis will:")
    print("  • Build your application")
    print("  • Upload to Firebase Storage")
    print("  • Clean up local files")
    print("  • Auto-increment version numbers")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
