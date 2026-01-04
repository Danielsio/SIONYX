"""
Chat Service - Client-side message handling

Uses Firebase SSE (Server-Sent Events) for real-time message updates.
This is much more efficient than polling - a single persistent connection
receives push notifications instantly when messages change.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from services.firebase_client import FirebaseClient, StreamListener
from utils.logger import get_logger


logger = get_logger(__name__)


class ChatService(QObject):
    """
    Service for handling chat messages on client side.

    Uses SSE (Server-Sent Events) for real-time updates instead of polling.
    Benefits:
    - Instant message notifications (no 5-60 second delay)
    - Single persistent connection (not repeated HTTP requests)
    - Minimal bandwidth (only sends changes, not full data)
    """

    # Qt signals for thread-safe communication
    messages_received = pyqtSignal(dict)  # Emitted when new messages are received

    def __init__(self, firebase_client: FirebaseClient, user_id: str, org_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.org_id = org_id
        self.is_listening = False

        # SSE stream listener (replaces polling thread)
        self._stream_listener: Optional[StreamListener] = None

        # Last seen update optimization
        self.last_seen_update_time = None
        self.last_seen_debounce_seconds = 60  # Only update every 60 seconds

        # Data caching - still useful for get_unread_messages() calls
        self.cached_messages: List[Dict] = []
        self.cache_timestamp: Optional[datetime] = None

        # Legacy callback support
        self._message_callback: Optional[Callable[[Dict], None]] = None

        logger.info(f"Chat service initialized for user {user_id} (SSE mode)")

    def get_unread_messages(self, use_cache: bool = True) -> Dict:
        """
        Get all unread messages for the current user.

        When SSE is active, the cache is kept up-to-date automatically.
        Falls back to HTTP GET when cache is empty or use_cache=False.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            {
                'success': bool,
                'messages': List[Dict] or [],
                'error': str (if failed)
            }
        """
        # Use cache if available and SSE is keeping it fresh
        if use_cache and self.cached_messages is not None and self.is_listening:
            logger.debug("Using SSE-cached messages")
            return {"success": True, "messages": self.cached_messages}

        # Also use cache if it's recent (within 10 seconds)
        if use_cache and self.cache_timestamp:
            cache_age = (datetime.now() - self.cache_timestamp).total_seconds()
            if cache_age < 10:
                logger.debug("Using recent cached messages")
                return {"success": True, "messages": self.cached_messages}

        logger.debug("Fetching unread messages via HTTP", action="get_messages")

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

        # Extract messages for this user
        user_messages = self._extract_user_messages(data)

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
        Start listening for new messages in real-time using SSE.

        This opens a persistent connection to Firebase that receives
        push notifications instantly when messages change - no polling!

        Args:
            callback: Optional callback function (deprecated, use signals instead)

        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_listening:
            logger.warning("Already listening for messages")
            return False

        self.is_listening = True
        self._message_callback = callback  # Keep for backward compatibility

        # Start SSE stream listener for messages path
        self._stream_listener = self.firebase.db_listen(
            path="messages",
            callback=self._on_stream_event,
            error_callback=self._on_stream_error,
        )

        logger.info("Started SSE listener for messages", action="start_listening")
        return True

    def stop_listening(self):
        """Stop listening for messages"""
        if not self.is_listening:
            return

        self.is_listening = False

        if self._stream_listener:
            self._stream_listener.stop()
            self._stream_listener = None

        logger.info("Stopped SSE listener for messages", action="stop_listening")

    def _on_stream_event(self, event_type: str, data: Any):
        """
        Handle SSE stream events from Firebase.

        Event types:
        - 'put': Initial data or data replaced at path
        - 'patch': Partial update to data
        - 'keep-alive': Connection heartbeat
        - 'cancel': Stream cancelled
        - 'auth_revoked': Auth token revoked
        """
        try:
            if event_type == "keep-alive":
                # Update last seen on keep-alive to show user is active
                self.update_last_seen()
                return

            if event_type in ("cancel", "auth_revoked"):
                logger.warning(f"SSE stream event: {event_type}")
                return

            if event_type not in ("put", "patch"):
                logger.debug(f"Unknown SSE event type: {event_type}")
                return

            # Extract messages data
            # SSE put/patch data format: {"path": "/...", "data": {...}}
            if not data:
                self._update_cache([])
                self._emit_messages([])
                return

            # Handle the data structure
            path = data.get("path", "/")
            payload = data.get("data")

            # Process messages based on event type and path
            if path == "/" and event_type == "put":
                # Full data replacement - payload is all messages
                messages = self._extract_user_messages(payload)
                self._update_cache(messages)
                self._emit_messages(messages)
            elif event_type == "patch" or path != "/":
                # Partial update - re-fetch full messages to ensure consistency
                # This is still efficient because it only happens on actual changes
                result = self.get_unread_messages(use_cache=False)
                if result.get("success"):
                    self._emit_messages(result.get("messages", []))

            # Update last seen timestamp (debounced)
            self.update_last_seen()

        except Exception as e:
            logger.error(f"Error processing SSE event: {e}")

    def _on_stream_error(self, error: str):
        """Handle SSE stream errors"""
        logger.error(f"SSE stream error: {error}")
        # The StreamListener handles reconnection automatically

    def _extract_user_messages(self, all_messages: Optional[Dict]) -> List[Dict]:
        """Extract unread messages for the current user from all messages"""
        if not all_messages or not isinstance(all_messages, dict):
            return []

        user_messages = []
        for message_id, message_data in all_messages.items():
            if not isinstance(message_data, dict):
                continue

            if message_data.get("toUserId") == self.user_id and not message_data.get(
                "read", False
            ):
                message_data["id"] = message_id
                user_messages.append(message_data)

        # Sort by timestamp (oldest first for display)
        user_messages.sort(key=lambda x: x.get("timestamp", ""))
        return user_messages

    def _emit_messages(self, messages: List[Dict]):
        """Emit messages via signal and callback"""
        result = {"success": True, "messages": messages}

        # Emit Qt signal for thread-safe UI updates
        self.messages_received.emit(result)

        # Call legacy callback if set
        if self._message_callback:
            try:
                self._message_callback(result)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")

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
        """Cleanup resources - stops SSE listener"""
        self.stop_listening()
        self.invalidate_cache()
        logger.info("Chat service cleaned up")
