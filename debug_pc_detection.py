#!/usr/bin/env python3
"""
Debug script to check PC detection and database state
Run this to diagnose why your PC usage isn't showing in admin dashboard
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.firebase_client import FirebaseClient
from utils.device_info import get_computer_info
from datetime import datetime
import json

def debug_pc_detection():
    """Debug PC detection and database state"""
    print("🔍 SIONYX PC Detection Debug Tool")
    print("=" * 50)
    
    # Initialize Firebase
    try:
        firebase = FirebaseClient()
        print("✅ Firebase connection established")
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return
    
    # Get current computer info
    print("\n📱 Current Computer Info:")
    print("-" * 30)
    try:
        computer_info = get_computer_info()
        print(f"Device ID: {computer_info.get('deviceId', 'Unknown')}")
        print(f"Computer Name: {computer_info.get('computerName', 'Unknown')}")
        print(f"MAC Address: {computer_info.get('macAddress', 'Unknown')}")
        print(f"OS: {computer_info.get('osInfo', {}).get('system', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to get computer info: {e}")
        return
    
    # Check if computer is registered
    print(f"\n💻 Computer Registration Status:")
    print("-" * 30)
    try:
        computer_id = computer_info.get('deviceId')
        computer_result = firebase.db_get(f'computers/{computer_id}')
        
        if computer_result.get('success') and computer_result.get('data'):
            computer_data = computer_result['data']
            print(f"✅ Computer is registered")
            print(f"   Name: {computer_data.get('computerName', 'Unknown')}")
            print(f"   Location: {computer_data.get('location', 'Not set')}")
            print(f"   Is Active: {computer_data.get('isActive', False)}")
            print(f"   Last Seen: {computer_data.get('lastSeen', 'Never')}")
            print(f"   Current User ID: {computer_data.get('currentUserId', 'None')}")
        else:
            print(f"❌ Computer is NOT registered in database")
            print(f"   Computer ID: {computer_id}")
    except Exception as e:
        print(f"❌ Failed to check computer registration: {e}")
    
    # Check all computers
    print(f"\n🖥️ All Computers in Database:")
    print("-" * 30)
    try:
        computers_result = firebase.db_get('computers')
        if computers_result.get('success') and computers_result.get('data'):
            computers = computers_result['data']
            print(f"Total computers: {len(computers)}")
            for comp_id, comp_data in computers.items():
                print(f"  - {comp_data.get('computerName', 'Unknown')} ({comp_id[:8]}...)")
                print(f"    Active: {comp_data.get('isActive', False)}")
                print(f"    User: {comp_data.get('currentUserId', 'None')}")
        else:
            print("❌ No computers found in database")
    except Exception as e:
        print(f"❌ Failed to get computers: {e}")
    
    # Check current user
    print(f"\n👤 Current User Status:")
    print("-" * 30)
    try:
        # Try to get current user from local storage or auth
        user_id = firebase.user_id
        if user_id:
            print(f"User ID: {user_id}")
            
            user_result = firebase.db_get(f'users/{user_id}')
            if user_result.get('success') and user_result.get('data'):
                user_data = user_result['data']
                print(f"✅ User found in database")
                print(f"   Name: {user_data.get('firstName', '')} {user_data.get('lastName', '')}")
                print(f"   Phone: {user_data.get('phoneNumber', 'Unknown')}")
                print(f"   Is Session Active: {user_data.get('isSessionActive', False)}")
                print(f"   Current Computer ID: {user_data.get('currentComputerId', 'None')}")
                print(f"   Current Computer Name: {user_data.get('currentComputerName', 'None')}")
                print(f"   Remaining Time: {user_data.get('remainingTime', 0)} seconds")
                print(f"   Last Activity: {user_data.get('lastActivity', 'Never')}")
                print(f"   Session Start Time: {user_data.get('sessionStartTime', 'Never')}")
            else:
                print(f"❌ User not found in database")
        else:
            print(f"❌ No user ID found (not logged in?)")
    except Exception as e:
        print(f"❌ Failed to check user status: {e}")
    
    # Check all users with active sessions
    print(f"\n👥 All Users with Active Sessions:")
    print("-" * 30)
    try:
        users_result = firebase.db_get('users')
        if users_result.get('success') and users_result.get('data'):
            users = users_result['data']
            active_users = []
            for uid, user_data in users.items():
                if user_data.get('isSessionActive', False):
                    active_users.append((uid, user_data))
            
            print(f"Active users: {len(active_users)}")
            for uid, user_data in active_users:
                print(f"  - {user_data.get('firstName', '')} {user_data.get('lastName', '')} ({uid[:8]}...)")
                print(f"    Computer: {user_data.get('currentComputerName', 'None')}")
                print(f"    Remaining Time: {user_data.get('remainingTime', 0)} seconds")
        else:
            print("❌ No users found in database")
    except Exception as e:
        print(f"❌ Failed to get users: {e}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    print("-" * 30)
    print("1. Make sure you're logged in on the PC client")
    print("2. Check if the PC client is running and connected")
    print("3. Verify Firebase credentials are correct")
    print("4. Check if there are any error messages in the PC client logs")
    print("5. Try logging out and logging back in on the PC client")
    
    print(f"\n🔧 Next Steps:")
    print("-" * 30)
    print("1. Run the PC client and log in")
    print("2. Check the PC client logs for any errors")
    print("3. Run this script again to see if data appears")
    print("4. If still no data, check Firebase console manually")

if __name__ == "__main__":
    debug_pc_detection()
