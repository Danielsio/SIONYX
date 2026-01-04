"""
Firebase Client - Realtime Database + Authentication
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
    """Firebase REST API client for Realtime Database"""

    def __init__(self):
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

        logger.info(
            "Firebase client initialized",
            org_id=self.org_id,
            component="firebase_client",
        )

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
        self._running = False

        # Close the response to unblock the iterator
        if self._response:
            try:
                self._response.close()
            except Exception:
                pass

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        logger.info(f"SSE listener stopped for path: {self.path}")

    def _listen_loop(self):
        """Main loop that maintains SSE connection with auto-reconnect"""
        while self._running:
            try:
                self._connect_and_stream()
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
        self._response = requests.get(
            url,
            params=params,
            headers=headers,
            stream=True,
            timeout=(10, None),  # 10s connect timeout, no read timeout
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
