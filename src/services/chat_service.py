"""
Chat Service - Client-side message handling
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal

from services.firebase_client import FirebaseClient
from utils.logger import get_logger

logger = get_logger(__name__)


class ChatService(QObject):
    """Service for handling chat messages on client side"""
    
    # Qt signals for thread-safe communication
    messages_received = pyqtSignal(dict)  # Emitted when new messages are received

    def __init__(self, firebase_client: FirebaseClient, user_id: str, org_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.org_id = org_id
        self.message_listeners = []
        self.is_listening = False
        self.listen_thread = None
        
        logger.info(f"Chat service initialized for user {user_id}")

    def get_unread_messages(self) -> Dict:
        """
        Get all unread messages for the current user
        
        Returns:
            {
                'success': bool,
                'messages': List[Dict] or [],
                'error': str (if failed)
            }
        """
        logger.info("Fetching unread messages")
        
        # Get all messages for this user
        result = self.firebase.db_get(f'messages')
        
        if not result.get('success'):
            logger.error(f"Failed to fetch messages: {result.get('error')}")
            return {
                'success': False,
                'messages': [],
                'error': result.get('error', 'Unknown error')
            }
        
        data = result.get('data')
        if not data:
            return {
                'success': True,
                'messages': []
            }
        
        # Filter messages for this user and unread status
        user_messages = []
        for message_id, message_data in data.items():
            if (message_data.get('toUserId') == self.user_id and 
                not message_data.get('read', False)):
                message_data['id'] = message_id
                user_messages.append(message_data)
        
        # Sort by timestamp (oldest first for display)
        user_messages.sort(key=lambda x: x.get('timestamp', ''))
        
        logger.info(f"Found {len(user_messages)} unread messages")
        return {
            'success': True,
            'messages': user_messages
        }

    def mark_message_as_read(self, message_id: str) -> Dict:
        """
        Mark a specific message as read
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            {
                'success': bool,
                'error': str (if failed)
            }
        """
        logger.info(f"Marking message {message_id} as read")
        
        result = self.firebase.db_set(f'messages/{message_id}/read', True)
        
        if not result.get('success'):
            logger.error(f"Failed to mark message as read: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error', 'Unknown error')
            }
        
        # Also set read timestamp
        read_timestamp = datetime.now().isoformat()
        timestamp_result = self.firebase.db_set(f'messages/{message_id}/readAt', read_timestamp)
        
        if not timestamp_result.get('success'):
            logger.warning(f"Failed to set read timestamp: {timestamp_result.get('error')}")
        
        logger.info(f"Message {message_id} marked as read")
        return {
            'success': True
        }

    def mark_all_messages_as_read(self) -> Dict:
        """
        Mark all unread messages for the current user as read
        
        Returns:
            {
                'success': bool,
                'error': str (if failed)
            }
        """
        logger.info("Marking all messages as read")
        
        # Get unread messages first
        unread_result = self.get_unread_messages()
        
        if not unread_result.get('success'):
            return unread_result
        
        messages = unread_result.get('messages', [])
        
        # Mark each message as read
        for message in messages:
            message_id = message.get('id')
            if message_id:
                self.mark_message_as_read(message_id)
        
        logger.info(f"Marked {len(messages)} messages as read")
        return {
            'success': True
        }

    def update_last_seen(self) -> Dict:
        """
        Update user's last seen timestamp to indicate they're active
        
        Returns:
            {
                'success': bool,
                'error': str (if failed)
            }
        """
        logger.debug("Updating last seen timestamp")
        
        last_seen = datetime.now().isoformat()
        result = self.firebase.db_set(f'users/{self.user_id}/lastSeen', last_seen)
        
        if not result.get('success'):
            logger.error(f"Failed to update last seen: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error', 'Unknown error')
            }
        
        return {
            'success': True
        }

    def start_listening(self, callback: Callable[[Dict], None] = None) -> bool:
        """
        Start listening for new messages in real-time
        
        Args:
            callback: Optional callback function (deprecated, use signals instead)
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_listening:
            logger.warning("Already listening for messages")
            return False
        
        self.is_listening = True
        self.message_callback = callback  # Keep for backward compatibility
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        logger.info("Started listening for messages")
        return True

    def stop_listening(self):
        """Stop listening for messages"""
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)
        
        logger.info("Stopped listening for messages")

    def _listen_loop(self):
        """Internal method for listening loop"""
        last_check = None
        
        while self.is_listening:
            try:
                # Get current messages
                result = self.get_unread_messages()
                
                if result.get('success'):
                    messages = result.get('messages', [])
                    
                    # Check if there are new messages
                    if last_check is None or len(messages) != last_check:
                        # Emit signal for thread-safe UI updates
                        self.messages_received.emit(result)
                        
                        # Also call callback for backward compatibility
                        if hasattr(self, 'message_callback') and self.message_callback:
                            self.message_callback(result)
                        last_check = len(messages)
                
                # Update last seen to show user is active
                self.update_last_seen()
                
                # Wait before next check (5 seconds)
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in message listening loop: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def is_user_active(self, last_seen: str) -> bool:
        """
        Check if user is considered active based on last seen timestamp
        
        Args:
            last_seen: ISO timestamp string
            
        Returns:
            bool: True if user is active (last seen within 5 minutes)
        """
        if not last_seen:
            return False
        
        try:
            last_seen_time = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            now = datetime.now(last_seen_time.tzinfo) if last_seen_time.tzinfo else datetime.now()
            diff_minutes = (now - last_seen_time).total_seconds() / 60
            
            return diff_minutes <= 5  # Active if last seen within 5 minutes
        except Exception as e:
            logger.error(f"Error parsing last seen timestamp: {str(e)}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        self.stop_listening()
        logger.info("Chat service cleaned up")
