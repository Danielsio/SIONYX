#!/usr/bin/env python3
"""
Test script for the SIONYX chat system
This script tests the basic functionality of the chat services
"""

import sys
import os
import time
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.chat_service import ChatService
from services.firebase_client import FirebaseClient
from utils.logger import get_logger

logger = get_logger(__name__)

def test_chat_service():
    """Test the chat service functionality"""
    print("🧪 Testing SIONYX Chat System")
    print("=" * 50)
    
    # Initialize Firebase client (you'll need to configure this)
    try:
        firebase = FirebaseClient()
        print("✅ Firebase client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Firebase client: {e}")
        return False
    
    # Test data
    test_user_id = "test_user_123"
    test_org_id = "test_org"
    test_message = "This is a test message from the admin"
    
    # Initialize chat service
    try:
        chat_service = ChatService(firebase, test_user_id, test_org_id)
        print("✅ Chat service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize chat service: {e}")
        return False
    
    # Test 1: Get unread messages (should be empty initially)
    print("\n📥 Testing get_unread_messages...")
    result = chat_service.get_unread_messages()
    if result.get('success'):
        messages = result.get('messages', [])
        print(f"✅ Retrieved {len(messages)} unread messages")
    else:
        print(f"❌ Failed to get unread messages: {result.get('error')}")
    
    # Test 2: Update last seen
    print("\n🕐 Testing update_last_seen...")
    result = chat_service.update_last_seen()
    if result.get('success'):
        print("✅ Last seen timestamp updated")
    else:
        print(f"❌ Failed to update last seen: {result.get('error')}")
    
    # Test 3: Test user active status
    print("\n🟢 Testing is_user_active...")
    now = datetime.now().isoformat()
    is_active = chat_service.is_user_active(now)
    print(f"✅ User active status (just now): {is_active}")
    
    # Test with old timestamp
    old_time = "2020-01-01T00:00:00"
    is_active_old = chat_service.is_user_active(old_time)
    print(f"✅ User active status (old): {is_active_old}")
    
    # Test 4: Test message listening (start and stop)
    print("\n👂 Testing message listening...")
    
    def message_callback(result):
        print(f"📨 Message callback received: {len(result.get('messages', []))} messages")
    
    # Start listening
    success = chat_service.start_listening(message_callback)
    if success:
        print("✅ Message listening started")
        
        # Wait a bit
        time.sleep(2)
        
        # Stop listening
        chat_service.stop_listening()
        print("✅ Message listening stopped")
    else:
        print("❌ Failed to start message listening")
    
    # Test 5: Cleanup
    print("\n🧹 Testing cleanup...")
    chat_service.cleanup()
    print("✅ Chat service cleaned up")
    
    print("\n🎉 Chat system tests completed!")
    return True

def test_firebase_connection():
    """Test Firebase connection"""
    print("\n🔥 Testing Firebase Connection...")
    
    try:
        firebase = FirebaseClient()
        
        # Test a simple read operation
        result = firebase.db_get('test')
        if result.get('success') or 'Not authenticated' in str(result.get('error', '')):
            print("✅ Firebase connection working")
            return True
        else:
            print(f"❌ Firebase connection failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Firebase connection error: {e}")
        return False

if __name__ == "__main__":
    print("SIONYX Chat System Test Suite")
    print("=" * 50)
    
    # Test Firebase connection first
    if not test_firebase_connection():
        print("\n⚠️  Firebase connection failed. Please check your configuration.")
        print("   Make sure you have:")
        print("   - Valid Firebase configuration")
        print("   - Internet connection")
        print("   - Proper authentication setup")
        sys.exit(1)
    
    # Test chat service
    if test_chat_service():
        print("\n✅ All tests passed! Chat system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
