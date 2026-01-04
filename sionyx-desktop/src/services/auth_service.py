"""
Authentication Service - Firebase Realtime Database
"""

from datetime import datetime
from typing import Dict, Optional

from database.local_db import LocalDatabase
from services.computer_service import ComputerService
from services.firebase_client import FirebaseClient
from utils.error_translations import translate_error
from utils.logger import get_logger


logger = get_logger(__name__)


class AuthService:
    """Authentication service using Firebase"""

    def __init__(self, config=None):
        self.config = config
        self.firebase = FirebaseClient()
        self.local_db = LocalDatabase()
        self.computer_service = ComputerService(self.firebase)
        self.current_user = None
        logger.info("Auth service initialized", component="auth_service")

    def is_logged_in(self) -> bool:
        """Check if user is already logged in"""
        stored_token = self.local_db.get_stored_token()

        if not stored_token:
            return False

        # Try to refresh token
        result = self.firebase.refresh_token_request(stored_token)

        if result.get("success"):
            # Load user data from Realtime Database
            user_result = self.firebase.db_get(f"users/{self.firebase.user_id}")

            if user_result.get("success") and user_result.get("data"):
                self.current_user = user_result["data"]
                self.current_user["uid"] = self.firebase.user_id
                logger.info(
                    "User auto-logged in",
                    user_id=self.firebase.user_id,
                    action="auto_login",
                )

                # Check for crashed/orphaned session and recover time
                self._recover_orphaned_session(self.firebase.user_id)

                # Register/update computer and associate with user
                self._handle_computer_registration(self.firebase.user_id)

                return True

        return False

    def login(self, phone: str, password: str) -> Dict:
        """
        Login with phone and password
        Phone is converted to email internally
        """
        logger.info(f"Login attempt for phone: {phone}")

        # Convert phone to email format
        email = self._phone_to_email(phone)

        # Sign in with Firebase Auth
        result = self.firebase.sign_in(email, password)

        if not result.get("success"):
            logger.warning(f"Login failed for {phone}")
            # Translate error message to Hebrew
            original_error = result.get("error", "Unknown error")
            translated_error = translate_error(original_error)
            result["error"] = translated_error
            return result

        uid = result["uid"]

        # Get user data from Realtime Database
        user_result = self.firebase.db_get(f"users/{uid}")

        if not user_result.get("success") or not user_result.get("data"):
            logger.error(f"User data not found for {uid}")
            return {"success": False, "error": translate_error("user data not found")}

        user_data = user_result["data"]

        # SINGLE SESSION ENFORCEMENT: Check if user is already logged in elsewhere
        if user_data.get("isLoggedIn") is True:
            current_computer_id = self.computer_service.get_computer_id()
            logged_in_computer = user_data.get("currentComputerId")
            
            # Allow re-login on the same computer, but reject login on different computer
            if logged_in_computer and logged_in_computer != current_computer_id:
                logger.warning(
                    f"Login rejected: User {uid} already logged in on computer {logged_in_computer}"
                )
                return {
                    "success": False,
                    "error": "המשתמש כבר מחובר במחשב אחר. יש להתנתק שם קודם.",
                }

        self.current_user = user_data
        self.current_user["uid"] = uid

        # Check for crashed/orphaned session and recover time
        self._recover_orphaned_session(uid)

        # Register/update computer and associate with user
        self._handle_computer_registration(uid)

        # Store credentials locally (encrypted)
        self.local_db.store_credentials(
            uid=uid,
            phone=phone,
            refresh_token=result["refresh_token"],
            user_data=self.current_user,
        )

        logger.info(f"Login successful for {phone}")
        return {"success": True, "user": self.current_user}

    def register(
        self,
        phone: str,
        password: str,
        first_name: str,
        last_name: str,
        email: str = "",
    ) -> Dict:
        """
        Register new user
        """
        logger.info(f"Registration attempt for phone: {phone}")

        # Validate inputs
        if len(password) < 6:
            return {
                "success": False,
                "error": translate_error("password must be at least 6 characters"),
            }

        # Convert phone to email format
        firebase_email = self._phone_to_email(phone)

        # Sign up with Firebase Auth
        result = self.firebase.sign_up(firebase_email, password)

        if not result.get("success"):
            logger.warning(f"Registration failed for {phone}")
            # Translate error message to Hebrew
            original_error = result.get("error", "Unknown error")
            translated_error = translate_error(original_error)
            result["error"] = translated_error
            return result

        uid = result["uid"]

        # Create user document in Realtime Database
        # Note: isSessionActive is set when a session starts (not here)
        # updatedAt is used for both session sync timing AND last activity
        user_data = {
            "firstName": first_name,
            "lastName": last_name,
            "phoneNumber": phone,
            "email": email if email else "",
            "remainingTime": 0,  # Start with 0 seconds
            "printBalance": 0.0,  # Start with 0 NIS print budget
            "isLoggedIn": False,  # User is not logged in until they log in
            "isAdmin": False,  # Regular users are not admins
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        # Save to database
        db_result = self.firebase.db_set(f"users/{uid}", user_data)

        if not db_result.get("success"):
            logger.error(f"Failed to create user data for {uid}")
            return {"success": False, "error": "Failed to create user profile"}

        self.current_user = user_data
        self.current_user["uid"] = uid

        # Store credentials locally
        self.local_db.store_credentials(
            uid=uid,
            phone=phone,
            refresh_token=result["refresh_token"],
            user_data=user_data,
        )

        # Register/update computer and associate with user (sets isLoggedIn=True)
        self._handle_computer_registration(uid)

        logger.info(f"Registration successful for {phone}")
        return {"success": True, "user": self.current_user}

    def logout(self):
        """Logout current user"""
        if self.current_user:
            user_id = self.current_user.get("uid")
            logger.info(f"User logged out: {user_id}")

            # Disassociate user from computer and mark as logged out
            current_computer_id = self.current_user.get("currentComputerId")
            if current_computer_id:
                self.computer_service.disassociate_user_from_computer(
                    user_id, current_computer_id, is_logout=True
                )
            else:
                # Even if no computer ID cached, still update isLoggedIn in DB
                self.firebase.db_update(
                    f"users/{user_id}",
                    {
                        "isLoggedIn": False,
                        "updatedAt": datetime.now().isoformat(),
                    },
                )

        self.firebase.id_token = None
        self.firebase.refresh_token = None
        self.firebase.user_id = None
        self.local_db.clear_tokens()
        self.current_user = None

    def get_current_user(self) -> Optional[Dict]:
        """Get current logged in user data"""
        return self.current_user

    def update_user_data(self, updates: Dict) -> Dict:
        """
        Update current user's data in database
        Example: {'remainingTime': 3600, 'printBalance': 50}
        """
        if not self.current_user:
            return {"success": False, "error": "No user logged in"}

        uid = self.current_user["uid"]

        # Add timestamp
        updates["updatedAt"] = datetime.now().isoformat()

        # Update in database
        result = self.firebase.db_update(f"users/{uid}", updates)

        if result.get("success"):
            # Update local cache
            self.current_user.update(updates)
            logger.info(f"User data updated for {uid}")

        return result

    def _recover_orphaned_session(self, user_id: str):
        """
        Clean up orphaned/crashed sessions WITHOUT deducting time.

        USER-FRIENDLY APPROACH:
        - Max "stolen" time is 60 seconds (one sync interval)
        - Could be innocent: power outage, crash, forgot to logout
        - Better to be forgiving than punish users for technical issues
        - Runs only on login (free, no extra cost)

        Uses updatedAt to detect stale sessions (updated every 60s during active session)
        """
        try:
            logger.info(f"Checking for orphaned session for user: {user_id}")

            # Get user data
            user_result = self.firebase.db_get(f"users/{user_id}")
            if not user_result.get("success") or not user_result.get("data"):
                return

            user_data = user_result["data"]
            is_session_active = user_data.get("isSessionActive", False)

            if not is_session_active:
                logger.debug("No active session to clean up")
                return

            # Use updatedAt to detect stale sessions (synced every 60s during session)
            updated_at_str = user_data.get("updatedAt")
            if not updated_at_str:
                logger.warning("Session has no updatedAt, cleaning up anyway")
                # Clean up session AND computer association (crashed = logged out)
                current_computer_id = user_data.get("currentComputerId")
                if current_computer_id:
                    self.computer_service.disassociate_user_from_computer(
                        user_id, current_computer_id, is_logout=True
                    )
                self.firebase.db_update(
                    f"users/{user_id}",
                    {
                        "isSessionActive": False,
                        "sessionStartTime": None,
                        "currentComputerId": None,
                        "updatedAt": datetime.now().isoformat(),
                    },
                )
                return

            # Calculate time since last update
            try:
                last_update = datetime.fromisoformat(updated_at_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid updatedAt format: {updated_at_str}")
                return

            now = datetime.now()
            time_since_update = (now - last_update).total_seconds()

            # If update is older than 2 minutes, session ended abnormally
            # (normal sync happens every 60s, so 2min = missed 2 syncs)
            if time_since_update > 120:  # 2 minutes
                logger.info(
                    f"🧹 Orphaned session detected "
                    f"({time_since_update:.0f}s since last sync)"
                )
                logger.info(
                    "Being kind: NOT deducting time (could be power outage/crash)"
                )
                logger.info("Max time 'lost': 60 seconds from last sync - acceptable!")

                # Clean up session AND computer association (crashed = logged out)
                current_computer_id = user_data.get("currentComputerId")
                if current_computer_id:
                    self.computer_service.disassociate_user_from_computer(
                        user_id, current_computer_id, is_logout=True
                    )
                self.firebase.db_update(
                    f"users/{user_id}",
                    {
                        "isSessionActive": False,
                        "sessionStartTime": None,
                        "currentComputerId": None,
                        "updatedAt": now.isoformat(),
                    },
                )

                logger.info("✅ Session and computer association cleaned up (no time deducted)")

            else:
                logger.debug(
                    f"Session is recent ({time_since_update:.0f}s old), "
                    f"no cleanup needed"
                )

        except Exception as e:
            logger.error(f"Failed to recover orphaned session: {e}")
            # Don't fail login if recovery fails

    def _handle_computer_registration(self, user_id: str):
        """
        Handle computer registration and user association
        Called during login to track which PC the user is using
        """
        try:
            logger.info("Handling computer registration for user login")

            # Register or update computer
            computer_result = self.computer_service.register_computer()

            if computer_result.get("success"):
                computer_id = computer_result["computer_id"]
                logger.info(f"Computer registered/updated: {computer_id}")

                # Associate user with computer and mark as logged in
                association_result = self.computer_service.associate_user_with_computer(
                    user_id, computer_id, is_login=True
                )

                if association_result.get("success"):
                    # CRITICAL: Update self.current_user so logout() can find the computer ID
                    if self.current_user:
                        self.current_user["currentComputerId"] = computer_id
                    logger.info(
                        f"User {user_id} associated with computer {computer_id}"
                    )
                else:
                    logger.warning(
                        f"Failed to associate user with computer: "
                        f"{association_result.get('error')}"
                    )
            else:
                logger.warning(
                    f"Computer registration failed: {computer_result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Computer registration failed: {e}")
            # Don't fail login if computer registration fails

    @staticmethod
    def _phone_to_email(phone: str) -> str:
        """
        Convert phone number to email format for Firebase
        Example: '1234567890' -> '1234567890@sionyx.app'
        """
        # Remove all non-digit characters
        clean_phone = "".join(filter(str.isdigit, phone))
        return f"{clean_phone}@sionyx.app"
