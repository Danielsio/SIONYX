"""
Computer/PC Management Service
Handles computer registration, tracking, and association with users
"""

from datetime import datetime
from typing import Dict

from services.firebase_client import FirebaseClient
from utils.device_info import get_computer_info
from utils.logger import get_logger


logger = get_logger(__name__)


class ComputerService:
    """Manages computer/PC registration and tracking"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client

    def register_computer(
        self, computer_name: str = None, location: str = None
    ) -> Dict:
        """
        Register the current computer in the organization

        Args:
            computer_name: Optional custom name for the computer
            location: Optional location description (e.g., "Lab A", "Room 101")

        Returns:
            {'success': bool, 'computer_id': str, 'error': str}
        """
        try:
            logger.debug("Registering computer", action="computer_registration")

            # Get computer information
            computer_info = get_computer_info()

            # Use provided name or generate one
            if computer_name:
                computer_info["computerName"] = computer_name
            elif (
                not computer_info.get("computerName")
                or computer_info["computerName"] == "Unknown-PC"
            ):
                computer_info["computerName"] = (
                    f"PC-{computer_info['deviceId'][:8].upper()}"
                )

            # Add location if provided
            if location:
                computer_info["location"] = location

            # Add timestamps
            now = datetime.now().isoformat()
            computer_info.update(
                {"createdAt": now, "updatedAt": now, "lastSeen": now, "isActive": True}
            )

            # Generate computer ID (use device ID as base)
            computer_id = computer_info["deviceId"]

            # Save to database
            result = self.firebase.db_set(f"computers/{computer_id}", computer_info)

            if not result.get("success"):
                logger.error("Failed to register computer")
                return {"success": False, "error": "Failed to register computer"}

            logger.info(
                "Computer registered successfully",
                computer_id=computer_id,
                action="computer_registration",
            )
            return {
                "success": True,
                "computer_id": computer_id,
                "computer_name": computer_info["computerName"],
            }

        except Exception as e:
            logger.error(
                "Computer registration failed",
                error=str(e),
                action="computer_registration",
            )
            return {"success": False, "error": str(e)}

    def get_computer_info(self, computer_id: str) -> Dict:
        """
        Get computer information by ID

        Args:
            computer_id: The computer ID to look up

        Returns:
            {'success': bool, 'data': dict, 'error': str}
        """
        try:
            result = self.firebase.db_get(f"computers/{computer_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to get computer info: {e}")
            return {"success": False, "error": str(e)}

    def update_computer_activity(self, computer_id: str) -> Dict:
        """
        Update computer's last seen timestamp

        Args:
            computer_id: The computer ID to update

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            now = datetime.now().isoformat()

            result = self.firebase.db_update(
                f"computers/{computer_id}",
                {"lastSeen": now, "updatedAt": now, "isActive": True},
            )

            return result

        except Exception as e:
            logger.error(f"Failed to update computer activity: {e}")
            return {"success": False, "error": str(e)}

    def associate_user_with_computer(self, user_id: str, computer_id: str) -> Dict:
        """
        Associate a user with a computer (when they log in)

        Args:
            user_id: The user ID
            computer_id: The computer ID

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            now = datetime.now().isoformat()

            # Get computer info for user record
            computer_result = self.get_computer_info(computer_id)
            if not computer_result.get("success"):
                return computer_result

            computer_data = computer_result["data"]
            computer_name = computer_data.get("computerName", "Unknown PC")

            # Update user record with computer association
            user_updates = {
                "currentComputerId": computer_id,
                "currentComputerName": computer_name,
                "lastComputerLogin": now,
                "updatedAt": now,
            }

            # Add to computer history (keep last 10)
            user_result = self.firebase.db_get(f"users/{user_id}")
            if user_result.get("success"):
                user_data = user_result["data"]
                computer_history = user_data.get("computerHistory", [])

                # Add current computer if not already in history
                if computer_id not in computer_history:
                    computer_history.insert(0, computer_id)  # Add to beginning
                    computer_history = computer_history[:10]  # Keep only last 10
                    user_updates["computerHistory"] = computer_history

            result = self.firebase.db_update(f"users/{user_id}", user_updates)

            if result.get("success"):
                # Also update computer with current user and mark as active
                self.firebase.db_update(
                    f"computers/{computer_id}",
                    {
                        "currentUserId": user_id,
                        "lastUserLogin": now,
                        "isActive": True,
                        "updatedAt": now,
                    },
                )

            return result

        except Exception as e:
            logger.error(f"Failed to associate user with computer: {e}")
            return {"success": False, "error": str(e)}

    def disassociate_user_from_computer(self, user_id: str, computer_id: str) -> Dict:
        """
        Disassociate a user from a computer (when they log out)

        Args:
            user_id: The user ID
            computer_id: The computer ID

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            now = datetime.now().isoformat()

            # Clear user's current computer
            user_result = self.firebase.db_update(
                f"users/{user_id}",
                {
                    "currentComputerId": None,
                    "currentComputerName": None,
                    "lastComputerLogout": now,
                    "updatedAt": now,
                },
            )

            # Clear computer's current user and mark as inactive
            computer_result = self.firebase.db_update(
                f"computers/{computer_id}",
                {
                    "currentUserId": None,
                    "lastUserLogout": now,
                    "isActive": False,
                    "updatedAt": now,
                },
            )

            return user_result if user_result.get("success") else computer_result

        except Exception as e:
            logger.error(f"Failed to disassociate user from computer: {e}")
            return {"success": False, "error": str(e)}

    def get_all_computers(self) -> Dict:
        """
        Get all computers in the organization

        Returns:
            {'success': bool, 'data': dict, 'error': str}
        """
        try:
            result = self.firebase.db_get("computers")
            return result

        except Exception as e:
            logger.error(f"Failed to get all computers: {e}")
            return {"success": False, "error": str(e)}

    def get_computer_usage_stats(self) -> Dict:
        """
        Get computer usage statistics for admin dashboard

        Returns:
            {'success': bool, 'data': dict, 'error': str}
        """
        try:
            # Get all computers
            computers_result = self.get_all_computers()
            if not computers_result.get("success"):
                return computers_result

            computers = computers_result.get("data") or {}

            # Get all users
            users_result = self.firebase.db_get("users")
            if not users_result.get("success"):
                return users_result

            users = users_result.get("data") or {}

            # Process statistics
            stats = {
                "total_computers": len(computers),
                "active_computers": 0,
                "computers_with_users": 0,
                "computer_details": [],
                "user_computer_usage": {},
            }

            for computer_id, computer_data in computers.items():
                is_active = computer_data.get("isActive", False)
                current_user_id = computer_data.get("currentUserId")

                if is_active:
                    stats["active_computers"] += 1

                if current_user_id:
                    stats["computers_with_users"] += 1

                    # Get user info
                    user_data = users.get(current_user_id, {})
                    first_name = user_data.get("firstName", "")
                    last_name = user_data.get("lastName", "")
                    user_name = f"{first_name} {last_name}".strip()

                    stats["computer_details"].append(
                        {
                            "computer_id": computer_id,
                            "computer_name": computer_data.get(
                                "computerName", "Unknown"
                            ),
                            "location": computer_data.get("location", ""),
                            "is_active": is_active,
                            "current_user_id": current_user_id,
                            "current_user_name": user_name,
                            "last_seen": computer_data.get("lastSeen", ""),
                            "os_info": computer_data.get("osInfo", {}),
                        }
                    )

                    # Track user's computer usage
                    if current_user_id not in stats["user_computer_usage"]:
                        stats["user_computer_usage"][current_user_id] = {
                            "user_name": user_name,
                            "computers_used": [],
                        }

                    stats["user_computer_usage"][current_user_id][
                        "computers_used"
                    ].append(
                        {
                            "computer_id": computer_id,
                            "computer_name": computer_data.get(
                                "computerName", "Unknown"
                            ),
                            "login_time": computer_data.get("lastUserLogin", ""),
                        }
                    )
                else:
                    # Computer without user
                    stats["computer_details"].append(
                        {
                            "computer_id": computer_id,
                            "computer_name": computer_data.get(
                                "computerName", "Unknown"
                            ),
                            "location": computer_data.get("location", ""),
                            "is_active": is_active,
                            "current_user_id": None,
                            "current_user_name": None,
                            "last_seen": computer_data.get("lastSeen", ""),
                            "os_info": computer_data.get("osInfo", {}),
                        }
                    )

            return {"success": True, "data": stats}

        except Exception as e:
            logger.error(f"Failed to get computer usage stats: {e}")
            return {"success": False, "error": str(e)}
