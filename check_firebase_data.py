#!/usr/bin/env python3
"""
Simple script to check Firebase database data
Run this to see what's actually in your Firebase database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.firebase_client import FirebaseClient
import json

def check_firebase_data():
    """Check Firebase database data"""
    print("🔥 Firebase Database Check")
    print("=" * 40)
    
    try:
        firebase = FirebaseClient()
        print("✅ Connected to Firebase")
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return
    
    # Check computers
    print("\n💻 Computers:")
    try:
        computers_result = firebase.db_get('computers')
        if computers_result.get('success') and computers_result.get('data'):
            computers = computers_result['data']
            print(f"Found {len(computers)} computers:")
            for comp_id, comp_data in computers.items():
                print(f"  {comp_id}:")
                print(f"    Name: {comp_data.get('computerName', 'Unknown')}")
                print(f"    Active: {comp_data.get('isActive', False)}")
                print(f"    Current User: {comp_data.get('currentUserId', 'None')}")
                print(f"    Last Seen: {comp_data.get('lastSeen', 'Never')}")
                print()
        else:
            print("❌ No computers found")
    except Exception as e:
        print(f"❌ Error getting computers: {e}")
    
    # Check users
    print("\n👥 Users:")
    try:
        users_result = firebase.db_get('users')
        if users_result.get('success') and users_result.get('data'):
            users = users_result['data']
            print(f"Found {len(users)} users:")
            for user_id, user_data in users.items():
                print(f"  {user_id}:")
                print(f"    Name: {user_data.get('firstName', '')} {user_data.get('lastName', '')}")
                print(f"    Phone: {user_data.get('phoneNumber', 'Unknown')}")
                print(f"    Session Active: {user_data.get('isSessionActive', False)}")
                print(f"    Current Computer: {user_data.get('currentComputerId', 'None')}")
                print(f"    Remaining Time: {user_data.get('remainingTime', 0)}")
                print(f"    Last Activity: {user_data.get('lastActivity', 'Never')}")
                print()
        else:
            print("❌ No users found")
    except Exception as e:
        print(f"❌ Error getting users: {e}")

if __name__ == "__main__":
    check_firebase_data()
