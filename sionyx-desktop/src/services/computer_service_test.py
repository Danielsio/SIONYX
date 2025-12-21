"""
Tests for ComputerService
"""

from datetime import datetime
from unittest.mock import patch, Mock

import pytest

from services.computer_service import ComputerService


class TestComputerService:
    """Test cases for ComputerService"""

    @pytest.fixture
    def computer_service(self, mock_firebase_client):
        """Create ComputerService instance with mocked dependencies"""
        return ComputerService(mock_firebase_client)

    @pytest.fixture
    def mock_computer_info(self):
        """Mock computer info data"""
        return {
            "deviceId": "abc123def456",
            "computerName": "TEST-PC",
            "osInfo": {"platform": "win32", "version": "10.0"},
            "macAddress": "AA:BB:CC:DD:EE:FF"
        }

    def test_initialization(self, computer_service, mock_firebase_client):
        """Test ComputerService initialization"""
        assert computer_service.firebase == mock_firebase_client

    def test_register_computer_success(self, computer_service, mock_firebase_client, mock_computer_info):
        """Test successful computer registration"""
        mock_firebase_client.db_set.return_value = {"success": True}
        
        with patch("services.computer_service.get_computer_info", return_value=mock_computer_info):
            result = computer_service.register_computer()
        
        assert result["success"] is True
        assert result["computer_id"] == mock_computer_info["deviceId"]
        assert result["computer_name"] == mock_computer_info["computerName"]

    def test_register_computer_with_custom_name(self, computer_service, mock_firebase_client, mock_computer_info):
        """Test computer registration with custom name"""
        mock_firebase_client.db_set.return_value = {"success": True}
        
        with patch("services.computer_service.get_computer_info", return_value=mock_computer_info):
            result = computer_service.register_computer(computer_name="My Custom PC")
        
        assert result["success"] is True
        assert result["computer_name"] == "My Custom PC"

    def test_register_computer_with_location(self, computer_service, mock_firebase_client, mock_computer_info):
        """Test computer registration with location"""
        mock_firebase_client.db_set.return_value = {"success": True}
        
        with patch("services.computer_service.get_computer_info", return_value=mock_computer_info):
            result = computer_service.register_computer(location="Lab A")
        
        assert result["success"] is True
        # Verify location was passed in the db_set call
        call_args = mock_firebase_client.db_set.call_args
        assert call_args[0][1].get("location") == "Lab A"

    def test_register_computer_unknown_pc_name(self, computer_service, mock_firebase_client):
        """Test computer registration with Unknown-PC name gets renamed"""
        mock_firebase_client.db_set.return_value = {"success": True}
        computer_info = {
            "deviceId": "abc123def456",
            "computerName": "Unknown-PC",
            "osInfo": {}
        }
        
        with patch("services.computer_service.get_computer_info", return_value=computer_info):
            result = computer_service.register_computer()
        
        assert result["success"] is True
        assert result["computer_name"].startswith("PC-")

    def test_register_computer_firebase_failure(self, computer_service, mock_firebase_client, mock_computer_info):
        """Test computer registration with Firebase failure"""
        mock_firebase_client.db_set.return_value = {"success": False, "error": "Database error"}
        
        with patch("services.computer_service.get_computer_info", return_value=mock_computer_info):
            result = computer_service.register_computer()
        
        assert result["success"] is False
        assert result["error"] == "Failed to register computer"

    def test_register_computer_exception(self, computer_service, mock_firebase_client):
        """Test computer registration with exception"""
        with patch("services.computer_service.get_computer_info", side_effect=Exception("Test error")):
            result = computer_service.register_computer()
        
        assert result["success"] is False
        assert "Test error" in result["error"]

    def test_get_computer_info_success(self, computer_service, mock_firebase_client):
        """Test getting computer info"""
        expected_data = {"computerName": "TEST-PC", "isActive": True}
        mock_firebase_client.db_get.return_value = {"success": True, "data": expected_data}
        
        result = computer_service.get_computer_info("computer-123")
        
        assert result["success"] is True
        assert result["data"] == expected_data
        mock_firebase_client.db_get.assert_called_with("computers/computer-123")

    def test_get_computer_info_exception(self, computer_service, mock_firebase_client):
        """Test getting computer info with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = computer_service.get_computer_info("computer-123")
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_update_computer_activity_success(self, computer_service, mock_firebase_client):
        """Test updating computer activity"""
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = computer_service.update_computer_activity("computer-123")
        
        assert result["success"] is True
        mock_firebase_client.db_update.assert_called_once()
        call_args = mock_firebase_client.db_update.call_args
        assert call_args[0][0] == "computers/computer-123"
        assert "lastSeen" in call_args[0][1]
        assert call_args[0][1]["isActive"] is True

    def test_update_computer_activity_exception(self, computer_service, mock_firebase_client):
        """Test updating computer activity with exception"""
        mock_firebase_client.db_update.side_effect = Exception("Update failed")
        
        result = computer_service.update_computer_activity("computer-123")
        
        assert result["success"] is False
        assert "Update failed" in result["error"]

    def test_associate_user_with_computer_success(self, computer_service, mock_firebase_client):
        """Test associating user with computer"""
        mock_firebase_client.db_get.side_effect = [
            # First call - get computer info
            {"success": True, "data": {"computerName": "TEST-PC"}},
            # Second call - get user info
            {"success": True, "data": {"computerHistory": []}}
        ]
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = computer_service.associate_user_with_computer("user-123", "computer-123")
        
        assert result["success"] is True
        # Should update both user and computer
        assert mock_firebase_client.db_update.call_count >= 1

    def test_associate_user_with_computer_not_found(self, computer_service, mock_firebase_client):
        """Test associating user with non-existent computer"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "Not found"}
        
        result = computer_service.associate_user_with_computer("user-123", "computer-123")
        
        assert result["success"] is False

    def test_associate_user_with_computer_updates_history(self, computer_service, mock_firebase_client):
        """Test that computer history is updated correctly"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {"computerName": "TEST-PC"}},
            {"success": True, "data": {"computerHistory": ["old-computer-1", "old-computer-2"]}}
        ]
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = computer_service.associate_user_with_computer("user-123", "new-computer")
        
        assert result["success"] is True
        # Check that history was updated
        user_update_call = mock_firebase_client.db_update.call_args_list[0]
        user_updates = user_update_call[0][1]
        assert user_updates.get("currentComputerId") == "new-computer"

    def test_associate_user_with_computer_exception(self, computer_service, mock_firebase_client):
        """Test association with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Database error")
        
        result = computer_service.associate_user_with_computer("user-123", "computer-123")
        
        assert result["success"] is False
        assert "Database error" in result["error"]

    def test_disassociate_user_from_computer_success(self, computer_service, mock_firebase_client):
        """Test disassociating user from computer"""
        mock_firebase_client.db_update.return_value = {"success": True}
        
        result = computer_service.disassociate_user_from_computer("user-123", "computer-123")
        
        assert result["success"] is True
        assert mock_firebase_client.db_update.call_count == 2  # User and computer updates

    def test_disassociate_user_from_computer_exception(self, computer_service, mock_firebase_client):
        """Test disassociation with exception"""
        mock_firebase_client.db_update.side_effect = Exception("Network error")
        
        result = computer_service.disassociate_user_from_computer("user-123", "computer-123")
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_get_all_computers_success(self, computer_service, mock_firebase_client):
        """Test getting all computers"""
        computers = {
            "comp-1": {"computerName": "PC-1"},
            "comp-2": {"computerName": "PC-2"}
        }
        mock_firebase_client.db_get.return_value = {"success": True, "data": computers}
        
        result = computer_service.get_all_computers()
        
        assert result["success"] is True
        assert result["data"] == computers
        mock_firebase_client.db_get.assert_called_with("computers")

    def test_get_all_computers_exception(self, computer_service, mock_firebase_client):
        """Test getting all computers with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = computer_service.get_all_computers()
        
        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_get_computer_usage_stats_success(self, computer_service, mock_firebase_client):
        """Test getting computer usage statistics"""
        computers = {
            "comp-1": {"computerName": "PC-1", "isActive": True, "currentUserId": "user-1"},
            "comp-2": {"computerName": "PC-2", "isActive": False, "currentUserId": None}
        }
        users = {
            "user-1": {"firstName": "John", "lastName": "Doe"}
        }
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": computers},
            {"success": True, "data": users}
        ]
        
        result = computer_service.get_computer_usage_stats()
        
        assert result["success"] is True
        stats = result["data"]
        assert stats["total_computers"] == 2
        assert stats["active_computers"] == 1
        assert stats["computers_with_users"] == 1

    def test_get_computer_usage_stats_empty(self, computer_service, mock_firebase_client):
        """Test getting stats when no computers exist"""
        mock_firebase_client.db_get.side_effect = [
            {"success": True, "data": {}},
            {"success": True, "data": {}}
        ]
        
        result = computer_service.get_computer_usage_stats()
        
        assert result["success"] is True
        stats = result["data"]
        assert stats["total_computers"] == 0
        assert stats["active_computers"] == 0

    def test_get_computer_usage_stats_computers_failure(self, computer_service, mock_firebase_client):
        """Test getting stats when fetching computers fails"""
        mock_firebase_client.db_get.return_value = {"success": False, "error": "Failed"}
        
        result = computer_service.get_computer_usage_stats()
        
        assert result["success"] is False

    def test_get_computer_usage_stats_exception(self, computer_service, mock_firebase_client):
        """Test getting stats with exception"""
        mock_firebase_client.db_get.side_effect = Exception("Network error")
        
        result = computer_service.get_computer_usage_stats()
        
        assert result["success"] is False
        assert "Network error" in result["error"]



