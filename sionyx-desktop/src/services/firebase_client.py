"""
Firebase Client - Realtime Database + Authentication

DESIGN PATTERN: Singleton
========================
This class uses the Singleton pattern to ensure only ONE instance exists.

WHY SINGLETON HERE?
- FirebaseClient holds authentication state (id_token, user_id, etc.)
- Multiple instances would have different auth states = bugs!
- All services need to share the SAME authenticated connection

HOW IT WORKS:
1. _instance: Class variable that stores the single instance
2. _lock: Thread lock to prevent race conditions
3. __new__: Called BEFORE __init__, controls object creation
4. If _instance exists, return it; otherwise create new one

USAGE:
    # All of these return the SAME instance:
    client1 = FirebaseClient()
    client2 = FirebaseClient()
    client3 = FirebaseClient.get_instance()
    assert client1 is client2 is client3  # True!
"""

import json
import threading
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

import requests

from utils.error_translations import translate_error
from utils.firebase_config import get_firebase_config
from utils.logger import get_logger


logger = get_logger(__name__)


class FirebaseClient:
    """
    Firebase REST API client for Realtime Database.

    This is a SINGLETON - only one instance will ever exist.
    Use FirebaseClient() or FirebaseClient.get_instance() to get it.
    """

    # ==================== SINGLETON PATTERN ====================
    #
    # These are CLASS variables (shared by all instances)
    # _instance: Holds the ONE instance of this class
    # _lock: Prevents two threads from creating instances simultaneously
    # _initialized: Prevents __init__ from running multiple times
    #
    _instance: Optional["FirebaseClient"] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> "FirebaseClient":
        """
        Control instance creation - this is called BEFORE __init__.

        __new__ is responsible for CREATING the object.
        __init__ is responsible for INITIALIZING the object.

        By overriding __new__, we can return an existing instance
        instead of creating a new one.
        """
        # Fast path: instance already exists, just return it
        # (no lock needed for reading)
        if cls._instance is not None:
            return cls._instance

        # Slow path: need to create instance
        # Use lock to prevent race condition where two threads
        # both see _instance as None and both try to create
        with cls._lock:
            # Double-check inside lock (another thread might have created it)
            if cls._instance is None:
                # Actually create the instance using parent's __new__
                cls._instance = super().__new__(cls)
                logger.debug("FirebaseClient singleton instance created")

        return cls._instance

    def __init__(self):
        """
        Initialize the Firebase client.

        NOTE: __init__ is called every time FirebaseClient() is used,
        even when returning existing instance. We use _initialized flag
        to ensure we only set up the client ONCE.
        """
        # Skip if already initialized (singleton protection)
        if FirebaseClient._initialized:
            return

        config = get_firebase_config()
        self.api_key = config.api_key
        self.database_url = config.database_url
        self.auth_url = config.auth_url

        # MULTI-TENANCY: Organization ID for data isolation
        self.org_id = config.org_id

        # Auth state
        self.id_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.user_id = None

        # Mark as initialized BEFORE logging (in case logging uses Firebase)
        FirebaseClient._initialized = True

        logger.info(
            "Firebase client initialized (singleton)",
            org_id=self.org_id,
            component="firebase_client",
        )

    @classmethod
    def get_instance(cls) -> "FirebaseClient":
        """
        Alternative way to get the singleton instance.

        This is more explicit than FirebaseClient() and makes
        the singleton pattern obvious to readers.

        Returns:
            The single FirebaseClient instance
        """
        return cls()

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance - FOR TESTING ONLY.

        This allows tests to start fresh with a new instance.
        Never use this in production code!
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False
            logger.debug("FirebaseClient singleton reset (testing)")

    # ==================== AUTHENTICATION ====================

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign up new user
        Email will be in format: phone@sionyx.app
        """
        url = f"{self.auth_url}:signUp?key={self.api_key}"

        payload = {"email": email, "password": password, "returnSecureToken": True}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self._store_auth_data(data)

            logger.info(
                "User signed up successfully", user_id=self.user_id, action="sign_up"
            )
            return {
                "success": True,
                "uid": self.user_id,
                "id_token": self.id_token,
                "refresh_token": self.refresh_token,
            }

        except requests.exceptions.RequestException as e:
            error_msg = self._parse_error(e)
            logger.error(
                "Sign up failed", error=str(e), error_msg=error_msg, action="sign_up"
            )
            return {"success": False, "error": error_msg}

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in existing user"""
        url = f"{self.auth_url}:signInWithPassword?key={self.api_key}"

        payload = {"email": email, "password": password, "returnSecureToken": True}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self._store_auth_data(data)

            logger.info(
                "User signed in successfully", user_id=self.user_id, action="sign_in"
            )
            return {
                "success": True,
                "uid": self.user_id,
                "id_token": self.id_token,
                "refresh_token": self.refresh_token,
            }

        except requests.exceptions.RequestException as e:
            error_msg = self._parse_error(e)
            logger.error(
                "Sign in failed", error=str(e), error_msg=error_msg, action="sign_in"
            )
            return {"success": False, "error": error_msg}

    def refresh_token_request(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh ID token"""
        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"

        payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.id_token = data["id_token"]
            self.refresh_token = data["refresh_token"]
            self.user_id = data["user_id"]
            self.token_expiry = datetime.now() + timedelta(
                seconds=int(data["expires_in"])
            )

            logger.info("Token refreshed successfully", action="token_refresh")
            return {
                "success": True,
                "id_token": self.id_token,
                "refresh_token": self.refresh_token,
            }

        except Exception as e:
            error_msg = self._parse_error(e)
            logger.error(
                "Token refresh failed",
                error=str(e),
                error_msg=error_msg,
                action="token_refresh",
            )
            return {"success": False, "error": error_msg}

    def _store_auth_data(self, data: Dict):
        """Store auth data from Firebase response"""
        self.id_token = data["idToken"]
        self.refresh_token = data["refreshToken"]
        self.user_id = data["localId"]
        self.token_expiry = datetime.now() + timedelta(seconds=int(data["expiresIn"]))

    def ensure_valid_token(self) -> bool:
        """Ensure token is valid, refresh if needed"""
        if not self.id_token or not self.refresh_token:
            return False

        # Refresh if expiring in next 5 minutes
        if datetime.now() >= self.token_expiry - timedelta(minutes=5):
            result = self.refresh_token_request(self.refresh_token)
            return result.get("success", False)

        return True

    # ==================== REALTIME DATABASE ====================

    def _get_org_path(self, path: str) -> str:
        """
        Prefix path with organization ID for multi-tenancy.

        MULTI-TENANCY ARCHITECTURE:
        - Each organization's data is isolated at: organizations/{orgId}/
        - Prevents accidental cross-org data access
        - Enables per-org security rules

        Examples:
            'users/abc123' → 'organizations/myorg/users/abc123'
            'packages' → 'organizations/myorg/packages'
        """
        # Remove leading/trailing slashes
        clean_path = path.strip("/")
        return f"organizations/{self.org_id}/{clean_path}"

    def db_get(self, path: str) -> Dict[str, Any]:
        """Get data from Realtime Database"""
        if not self.ensure_valid_token():
            return {"success": False, "error": "Not authenticated"}

        # MULTI-TENANCY: Automatically prefix with org path
        org_path = self._get_org_path(path)
        url = f"{self.database_url}/{org_path}.json"
        params = {"auth": self.id_token}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.debug("Database read completed", path=org_path, action="db_get")

            return {"success": True, "data": data}

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(
                "Database read failed", path=org_path, error=error_msg, action="db_get"
            )
            return {"success": False, "error": error_msg}

    def db_set(self, path: str, data: Any) -> Dict[str, Any]:
        """
        Set data in Realtime Database (overwrites)
        Path example: 'users/user123'
        """
        if not self.ensure_valid_token():
            return {"success": False, "error": "Not authenticated"}

        # MULTI-TENANCY: Automatically prefix with org path
        org_path = self._get_org_path(path)
        url = f"{self.database_url}/{org_path}.json"
        params = {"auth": self.id_token}

        try:
            response = requests.put(url, params=params, json=data, timeout=10)
            response.raise_for_status()

            logger.debug("Database write completed", path=org_path, action="db_set")
            return {"success": True, "data": response.json()}

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(
                "Database write failed", path=org_path, error=error_msg, action="db_set"
            )
            return {"success": False, "error": error_msg}

    def db_update(self, path: str, data: Dict) -> Dict[str, Any]:
        """
        Update data in Realtime Database (merge, don't overwrite)
        Path example: 'users/user123'
        """
        if not self.ensure_valid_token():
            return {"success": False, "error": "Not authenticated"}

        # MULTI-TENANCY: Automatically prefix with org path
        org_path = self._get_org_path(path)
        url = f"{self.database_url}/{org_path}.json"
        params = {"auth": self.id_token}

        try:
            response = requests.patch(url, params=params, json=data, timeout=10)
            response.raise_for_status()

            logger.debug("Database update completed", path=org_path, action="db_update")
            return {"success": True, "data": response.json()}

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(
                "Database update failed",
                path=org_path,
                error=error_msg,
                action="db_update",
            )
            return {"success": False, "error": error_msg}

    def db_delete(self, path: str) -> Dict[str, Any]:
        """
        Delete data from Realtime Database
        """
        if not self.ensure_valid_token():
            return {"success": False, "error": "Not authenticated"}

        # MULTI-TENANCY: Automatically prefix with org path
        org_path = self._get_org_path(path)
        url = f"{self.database_url}/{org_path}.json"
        params = {"auth": self.id_token}

        try:
            response = requests.delete(url, params=params, timeout=10)
            response.raise_for_status()

            logger.debug("Database delete completed", path=org_path, action="db_delete")
            return {"success": True}

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(
                "Database delete failed",
                path=org_path,
                error=error_msg,
                action="db_delete",
            )
            return {"success": False, "error": error_msg}

    # ==================== REAL-TIME STREAMING (SSE) ====================

    def db_listen(
        self,
        path: str,
        callback: Callable[[str, Any], None],
        error_callback: Optional[Callable[[str], None]] = None,
    ) -> "StreamListener":
        """
        Listen to real-time changes on a database path using Server-Sent Events (SSE).

        This is MUCH more efficient than polling:
        - Single persistent connection instead of repeated HTTP requests
        - Instant push notifications when data changes
        - Minimal bandwidth usage (only sends changes)

        Args:
            path: Database path to listen to (e.g., 'messages')
            callback: Function called with (event_type, data) when data changes
                     event_type: 'put', 'patch', 'keep-alive', 'cancel', 'auth_revoked'
            error_callback: Optional function called with error message on connection issues

        Returns:
            StreamListener object with stop() method to end the subscription

        Usage:
            def on_message(event, data):
                if event == 'put':
                    print(f"Data changed: {data}")

            listener = firebase.db_listen('messages', on_message)
            # ... later ...
            listener.stop()
        """
        listener = StreamListener(
            firebase_client=self,
            path=path,
            callback=callback,
            error_callback=error_callback,
        )
        listener.start()
        return listener

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _parse_error(exception: Exception) -> str:
        """Parse Firebase error to user-friendly message"""
        if hasattr(exception, "response") and exception.response is not None:
            try:
                error_data = exception.response.json()
                if "error" in error_data:
                    message = error_data["error"].get("message", "")

                    # Map Firebase errors to common error types for translation
                    if "EMAIL_EXISTS" in message:
                        return translate_error("email already exists")
                    elif "INVALID_PASSWORD" in message or "EMAIL_NOT_FOUND" in message:
                        return translate_error("invalid credentials")
                    elif "INVALID_LOGIN_CREDENTIALS" in message:
                        return translate_error("invalid credentials")
                    elif "WEAK_PASSWORD" in message:
                        return translate_error("password too weak")
                    elif "TOO_MANY_ATTEMPTS" in message:
                        return translate_error("too many attempts")
                    elif "USER_DISABLED" in message:
                        return translate_error("account disabled")
                    elif "INVALID_EMAIL" in message:
                        return translate_error("invalid input")
                    elif "MISSING_PASSWORD" in message:
                        return translate_error("required field")
                    elif "OPERATION_NOT_ALLOWED" in message:
                        return translate_error("access denied")

                    # For any other Firebase error, try to translate it
                    return translate_error(message)
            except Exception:
                pass

        # For non-Firebase errors, try to translate them too
        return translate_error(str(exception))


class StreamListener:
    """
    Server-Sent Events (SSE) listener for Firebase Realtime Database.

    Firebase REST API supports streaming via SSE:
    - Uses 'Accept: text/event-stream' header
    - Single persistent HTTP connection
    - Receives push notifications for data changes
    - Events: 'put' (data set), 'patch' (data updated), 'keep-alive', 'cancel', 'auth_revoked'
    """

    def __init__(
        self,
        firebase_client: FirebaseClient,
        path: str,
        callback: Callable[[str, Any], None],
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        self.firebase = firebase_client
        self.path = path
        self.callback = callback
        self.error_callback = error_callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._response: Optional[requests.Response] = None
        self._reconnect_delay = 1  # Start with 1 second
        self._max_reconnect_delay = 60  # Max 60 seconds between reconnects

    def start(self):
        """Start the SSE listener in a background thread"""
        if self._running:
            logger.warning("Stream listener already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info(f"SSE listener started for path: {self.path}")

    def stop(self):
        """Stop the SSE listener"""
        logger.debug(f"StreamListener.stop() called for path: {self.path}")
        self._running = False

        # DON'T close the response from another thread - it causes crashes!
        # The thread will exit naturally when:
        # 1. It checks self._running after receiving data
        # 2. The read timeout occurs and it checks self._running
        # 3. The connection is closed by the server

        # Wait briefly for the thread to notice the flag change
        if self._thread and self._thread.is_alive():
            logger.debug(f"Waiting for SSE thread to finish (path: {self.path})...")
            self._thread.join(timeout=0.5)
            if self._thread.is_alive():
                logger.debug(
                    f"SSE thread still running, will exit on next timeout "
                    f"(path: {self.path})"
                )

        logger.info(f"SSE listener stopped for path: {self.path}")

    def _listen_loop(self):
        """Main loop that maintains SSE connection with auto-reconnect"""
        while self._running:
            try:
                self._connect_and_stream()
            except requests.exceptions.ReadTimeout:
                # This is expected - we use timeout to allow checking _running flag
                logger.debug(f"SSE read timeout for path: {self.path} (checking flag)")
                continue
            except Exception as e:
                if not self._running:
                    break

                error_msg = str(e)
                logger.error(f"SSE connection error: {error_msg}")

                if self.error_callback:
                    try:
                        self.error_callback(error_msg)
                    except Exception:
                        pass

                # Exponential backoff for reconnection
                if self._running:
                    logger.info(
                        f"Reconnecting in {self._reconnect_delay}s...",
                        path=self.path,
                    )
                    # Use small sleep intervals to check _running flag
                    for _ in range(int(self._reconnect_delay * 10)):
                        if not self._running:
                            break
                        threading.Event().wait(0.1)

                    self._reconnect_delay = min(
                        self._reconnect_delay * 2, self._max_reconnect_delay
                    )

    def _connect_and_stream(self):
        """Establish SSE connection and process events"""
        # Ensure valid token before connecting
        if not self.firebase.ensure_valid_token():
            raise ConnectionError("Not authenticated")

        org_path = self.firebase._get_org_path(self.path)
        url = f"{self.firebase.database_url}/{org_path}.json"

        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }

        params = {"auth": self.firebase.id_token}

        logger.debug(f"Connecting SSE stream to: {org_path}")

        # Use stream=True for SSE
        # Add read timeout so thread can check _running flag periodically
        self._response = requests.get(
            url,
            params=params,
            headers=headers,
            stream=True,
            timeout=(10, 60),  # 10s connect timeout, 60s read timeout
        )
        self._response.raise_for_status()

        # Reset reconnect delay on successful connection
        self._reconnect_delay = 1

        logger.info(f"SSE stream connected: {org_path}")

        # Process SSE events
        event_type = None
        data_lines = []

        for line in self._response.iter_lines(decode_unicode=True):
            if not self._running:
                break

            if line is None:
                continue

            line = line.strip()

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())
            elif line == "" and event_type:
                # Empty line signals end of event
                self._process_event(event_type, "".join(data_lines))
                event_type = None
                data_lines = []

    def _process_event(self, event_type: str, data_str: str):
        """Process a single SSE event"""
        try:
            if event_type == "keep-alive":
                # Firebase sends keep-alive to maintain connection
                logger.debug("SSE keep-alive received")
                return

            if event_type == "cancel":
                logger.warning("SSE stream cancelled by server")
                self.callback(event_type, None)
                return

            if event_type == "auth_revoked":
                logger.warning("SSE auth revoked - need to re-authenticate")
                self.callback(event_type, None)
                return

            # Parse JSON data for put/patch events
            if data_str:
                data = json.loads(data_str)
                self.callback(event_type, data)
            else:
                self.callback(event_type, None)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SSE data: {e}, raw: {data_str[:100]}")
        except Exception as e:
            logger.error(f"Error processing SSE event: {e}")
