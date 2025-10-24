#!/usr/bin/env python3
"""
Check available Firebase Storage buckets
"""

import os
import json
from pathlib import Path

def check_firebase_buckets():
    """Check available Firebase Storage buckets"""
    print("Checking Firebase Storage buckets...")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, storage
    except ImportError:
        print("❌ Firebase Admin SDK not installed")
        print("Install with: pip install firebase-admin")
        return
    
    # Find service account key
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
        print("❌ Firebase service account key not found")
        print("Please place your service account JSON file as 'serviceAccountKey.json'")
        return
    
    try:
        # Initialize Firebase Admin with different bucket name formats
        cred = credentials.Certificate(service_account_path)
        
        # Try different bucket name formats
        bucket_formats = [
            "sionyx-19636.appspot.com",
            "sionyx-19636",
            "sionyx-19636.firebasestorage.app"
        ]
        
        print("✅ Firebase Admin initialized")
        print("Testing different bucket name formats:")
        
        for bucket_name in bucket_formats:
            try:
                # Initialize with specific bucket
                app = firebase_admin.initialize_app(cred, {
                    'storageBucket': bucket_name
                }, name=f"test_{bucket_name.replace('.', '_')}")
                
                # Try to access the bucket
                bucket = storage.bucket(app=app)
                print(f"  ✅ Bucket '{bucket_name}' - SUCCESS")
                print(f"     📦 Bucket name: {bucket.name}")
                print(f"     🌐 Bucket URL: https://console.firebase.google.com/project/sionyx-19636/storage")
                
                # Clean up the app
                firebase_admin.delete_app(app)
                break
                
            except Exception as e:
                print(f"  ❌ Bucket '{bucket_name}' - FAILED: {e}")
                # Clean up the app if it was created
                try:
                    firebase_admin.delete_app(app)
                except:
                    pass
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_firebase_buckets()
