"""
Chat Service - Client-side message handling
"""

import threading
import time
from datetime import datetime
from typing import Callable, Dict, List

from PyQt6.QtCore import QObject, pyqtSignal

from src.services.firebase_client import FirebaseClient
from src.utils.logger import get_logger


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

        # Smart polling configuration
        self.base_poll_interval = 5  # Base interval in seconds
        self.max_poll_interval = 60  # Maximum interval in seconds
        self.current_poll_interval = self.base_poll_interval
        self.consecutive_empty_polls = 0
        self.max_empty_polls = 3  # After 3 empty polls, increase interval

        # Last seen update optimization
        self.last_seen_update_time = None
        self.last_seen_debounce_seconds = 30  # Only update every 30 seconds

        # Data caching
        self.cached_messages = []
        self.cache_timestamp = None
        self.cache_duration_seconds = 10  # Cache for 10 seconds

        logger.info(f"Chat service initialized for user {user_id}")

    def get_unread_messages(self, use_cache: bool = True) -> Dict:
        """
        Get all unread messages for the current user with caching

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            {
                'success': bool,
                'messages': List[Dict] or [],
                'error': str (if failed)
            }
        """
        # Check cache first if enabled
        if use_cache and self._is_cache_valid():
            logger.debug("Using cached messages")
            return {"success": True, "messages": self.cached_messages}

        logger.debug("Fetching unread messages", action="get_messages")

        # Get all messages for this user (Firebase client handles org path)
        result = self.firebase.db_get("messages")

        if not result.get("success"):
            logger.error(f"Failed to fetch messages: {result.get('error')}")
            return {
                "success": False,
                "messages": [],
                "error": result.get("error", "Unknown error"),
            }

        data = result.get("data")
        if not data:
            self._update_cache([])
            return {"success": True, "messages": []}

        # Filter messages for this user and unread status
        user_messages = []
        for message_id, message_data in data.items():
            if message_data.get("toUserId") == self.user_id and not message_data.get(
                "read", False
            ):
                message_data["id"] = message_id
                user_messages.append(message_data)

        # Sort by timestamp (oldest first for display)
        user_messages.sort(key=lambda x: x.get("timestamp", ""))

        # Update cache
        self._update_cache(user_messages)

        logger.debug(
            "Found unread messages", count=len(user_messages), action="get_messages"
        )
        return {"success": True, "messages": user_messages}

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
        logger.debug(
            "Marking message as read", message_id=message_id, action="mark_read"
        )

        result = self.firebase.db_set(f"messages/{message_id}/read", True)

        if not result.get("success"):
            logger.error(f"Failed to mark message as read: {result.get('error')}")
            return {"success": False, "error": result.get("error", "Unknown error")}

        # Also set read timestamp
        read_timestamp = datetime.now().isoformat()
        timestamp_result = self.firebase.db_set(
            f"messages/{message_id}/readAt", read_timestamp
        )

        if not timestamp_result.get("success"):
            logger.warning(
                f"Failed to set read timestamp: {timestamp_result.get('error')}"
            )

        logger.debug(
            "Message marked as read", message_id=message_id, action="mark_read"
        )
        return {"success": True}

    def mark_all_messages_as_read(self) -> Dict:
        """
        Mark all unread messages for the current user as read

        Returns:
            {
                'success': bool,
                'error': str (if failed)
            }
        """
        logger.debug("Marking all messages as read", action="mark_all_read")

        # Get unread messages first
        unread_result = self.get_unread_messages()

        if not unread_result.get("success"):
            return unread_result

        messages = unread_result.get("messages", [])

        # Mark each message as read
        for message in messages:
            message_id = message.get("id")
            if message_id:
                self.mark_message_as_read(message_id)

        logger.debug(
            "Marked all messages as read", count=len(messages), action="mark_all_read"
        )
        return {"success": True}

    def update_last_seen(self, force: bool = False) -> Dict:
        """
        Update user's last seen timestamp to indicate they're active
        Uses debouncing to avoid excessive API calls

        Args:
            force: Force update regardless of debounce timing

        Returns:
            {
                'success': bool,
                'error': str (if failed)
            }
        """
        now = datetime.now()

        # Check if we should skip this update due to debouncing
        if not force and self.last_seen_update_time:
            time_since_last_update = (now - self.last_seen_update_time).total_seconds()
            if time_since_last_update < self.last_seen_debounce_seconds:
                logger.debug(
                    f"Skipping last seen update (debounced, "
                    f"{time_since_last_update:.1f}s since last)"
                )
                return {"success": True, "skipped": True}

        logger.debug("Updating last seen timestamp")

        last_seen = now.isoformat()
        result = self.firebase.db_set(f"users/{self.user_id}/lastSeen", last_seen)

        if not result.get("success"):
            logger.error(f"Failed to update last seen: {result.get('error')}")
            return {"success": False, "error": result.get("error", "Unknown error")}

        # Update our tracking timestamp
        self.last_seen_update_time = now

        return {"success": True}

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

        logger.debug("Started listening for messages", action="start_listening")
        return True

    def stop_listening(self):
        """Stop listening for messages"""
        if not self.is_listening:
            return

        self.is_listening = False

        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)

        logger.debug("Stopped listening for messages", action="stop_listening")

    def _listen_loop(self):
        """Internal method for listening loop with smart polling"""
        last_check = None

        while self.is_listening:
            try:
                # Get current messages (use cache for efficiency)
                result = self.get_unread_messages(use_cache=True)

                if result.get("success"):
                    messages = result.get("messages", [])
                    message_count = len(messages)

                    # Check if there are new messages
                    if last_check is None or message_count != last_check:
                        # Emit signal for thread-safe UI updates
                        self.messages_received.emit(result)

                        # Also call callback for backward compatibility
                        if hasattr(self, "message_callback") and self.message_callback:
                            self.message_callback(result)
                        last_check = message_count

                        # Reset polling interval when we find messages
                        self.current_poll_interval = self.base_poll_interval
                        self.consecutive_empty_polls = 0
                    else:
                        # No new messages, increment empty poll counter
                        self.consecutive_empty_polls += 1

                        # Increase polling interval if we've had many empty polls
                        if self.consecutive_empty_polls >= self.max_empty_polls:
                            self.current_poll_interval = min(
                                self.current_poll_interval * 1.5, self.max_poll_interval
                            )
                            logger.debug(
                                f"Increased polling interval to "
                                f"{self.current_poll_interval:.1f}s"
                            )

                # Update last seen to show user is active (with debouncing)
                self.update_last_seen()

                # Wait before next check with dynamic interval
                time.sleep(self.current_poll_interval)

            except Exception as e:
                logger.error(f"Error in message listening loop: {str(e)}")
                # Use base interval for retry
                time.sleep(self.base_poll_interval)

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
            last_seen_time = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            now = (
                datetime.now(last_seen_time.tzinfo)
                if last_seen_time.tzinfo
                else datetime.now()
            )
            diff_minutes = (now - last_seen_time).total_seconds() / 60

            return diff_minutes <= 5  # Active if last seen within 5 minutes
        except Exception as e:
            logger.error(f"Error parsing last seen timestamp: {str(e)}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cache_timestamp or not self.cached_messages:
            return False

        now = datetime.now()
        cache_age = (now - self.cache_timestamp).total_seconds()
        return cache_age < self.cache_duration_seconds

    def _update_cache(self, messages: List[Dict]):
        """Update the message cache with new data"""
        self.cached_messages = messages
        self.cache_timestamp = datetime.now()
        logger.debug(f"Updated message cache with {len(messages)} messages")

    def invalidate_cache(self):
        """Invalidate the message cache to force fresh data on next request"""
        self.cached_messages = []
        self.cache_timestamp = None
        logger.debug("Message cache invalidated")

    def cleanup(self):
        """Cleanup resources"""
        self.stop_listening()
        logger.info("Chat service cleaned up")
