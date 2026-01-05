"""
Tests for organization_metadata_service.py
Tests organization metadata fetching, decoding, and pricing management.
"""

import base64
import json
from unittest.mock import Mock, patch

import pytest

from services.organization_metadata_service import OrganizationMetadataService


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_firebase():
    """Create a mock FirebaseClient"""
    return Mock()


@pytest.fixture
def metadata_service(mock_firebase):
    """Create OrganizationMetadataService with mocked dependencies"""
    with patch("services.organization_metadata_service.get_logger") as mock_logger:
        mock_logger.return_value = Mock()
        return OrganizationMetadataService(firebase_client=mock_firebase)


@pytest.fixture
def encoded_mosad_id():
    """Create base64 encoded mosad ID"""
    data = "mosad123"
    return base64.b64encode(json.dumps(data).encode()).decode()


@pytest.fixture
def encoded_api_valid():
    """Create base64 encoded API valid key"""
    data = "api_key_valid_123"
    return base64.b64encode(json.dumps(data).encode()).decode()


@pytest.fixture
def sample_metadata(encoded_mosad_id, encoded_api_valid):
    """Sample organization metadata"""
    return {
        "name": "Test Organization",
        "nedarim_mosad_id": encoded_mosad_id,
        "nedarim_api_valid": encoded_api_valid,
        "created_at": "2024-01-01T00:00:00",
        "status": "active",
    }


# =============================================================================
# Initialization tests
# =============================================================================
class TestOrganizationMetadataServiceInit:
    """Tests for service initialization"""

    def test_initialization_stores_firebase_client(self, mock_firebase):
        """Test service stores firebase client"""
        with patch("services.organization_metadata_service.get_logger"):
            service = OrganizationMetadataService(firebase_client=mock_firebase)
            assert service.firebase == mock_firebase


# =============================================================================
# decode_data tests
# =============================================================================
class TestDecodeData:
    """Tests for decode_data method"""

    def test_decode_valid_base64_string(self, metadata_service):
        """Test decoding valid base64 encoded string"""
        original = "test_value"
        encoded = base64.b64encode(json.dumps(original).encode()).decode()

        result = metadata_service.decode_data(encoded)
        assert result == original

    def test_decode_valid_base64_dict(self, metadata_service):
        """Test decoding base64 encoded dictionary"""
        original = {"key": "value", "number": 42}
        encoded = base64.b64encode(json.dumps(original).encode()).decode()

        result = metadata_service.decode_data(encoded)
        assert result == original

    def test_decode_valid_base64_list(self, metadata_service):
        """Test decoding base64 encoded list"""
        original = [1, 2, 3, "four"]
        encoded = base64.b64encode(json.dumps(original).encode()).decode()

        result = metadata_service.decode_data(encoded)
        assert result == original

    def test_decode_invalid_base64(self, metadata_service):
        """Test decoding invalid base64 returns None"""
        result = metadata_service.decode_data("not_valid_base64!!!")
        assert result is None

    def test_decode_invalid_json(self, metadata_service):
        """Test decoding valid base64 but invalid JSON returns None"""
        encoded = base64.b64encode(b"not json").decode()
        result = metadata_service.decode_data(encoded)
        assert result is None

    def test_decode_empty_string(self, metadata_service):
        """Test decoding empty string returns None"""
        result = metadata_service.decode_data("")
        assert result is None


# =============================================================================
# get_organization_metadata tests
# =============================================================================
class TestGetOrganizationMetadata:
    """Tests for get_organization_metadata method"""

    def test_get_metadata_success(
        self, metadata_service, mock_firebase, sample_metadata
    ):
        """Test successful metadata retrieval"""
        mock_firebase.db_get.return_value = {"success": True, "data": sample_metadata}

        result = metadata_service.get_organization_metadata("org123")

        assert result["success"] is True
        assert "metadata" in result

    def test_get_metadata_returns_name(
        self, metadata_service, mock_firebase, sample_metadata
    ):
        """Test metadata includes organization name"""
        mock_firebase.db_get.return_value = {"success": True, "data": sample_metadata}

        result = metadata_service.get_organization_metadata("org123")

        assert result["metadata"]["name"] == "Test Organization"

    def test_get_metadata_returns_status(
        self, metadata_service, mock_firebase, sample_metadata
    ):
        """Test metadata includes status"""
        mock_firebase.db_get.return_value = {"success": True, "data": sample_metadata}

        result = metadata_service.get_organization_metadata("org123")

        assert result["metadata"]["status"] == "active"

    def test_get_metadata_decodes_credentials(
        self, metadata_service, mock_firebase, sample_metadata
    ):
        """Test metadata decodes NEDARIM credentials"""
        mock_firebase.db_get.return_value = {"success": True, "data": sample_metadata}

        result = metadata_service.get_organization_metadata("org123")

        assert result["metadata"]["nedarim_mosad_id"] == "mosad123"
        assert result["metadata"]["nedarim_api_valid"] == "api_key_valid_123"

    def test_get_metadata_firebase_failure(self, metadata_service, mock_firebase):
        """Test handling of Firebase failure"""
        mock_firebase.db_get.return_value = {"success": False, "error": "Network error"}

        result = metadata_service.get_organization_metadata("org123")

        assert result["success"] is False
        assert "error" in result

    def test_get_metadata_no_data(self, metadata_service, mock_firebase):
        """Test handling of empty data"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}

        result = metadata_service.get_organization_metadata("org123")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_metadata_missing_credentials(self, metadata_service, mock_firebase):
        """Test handling of missing NEDARIM credentials"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"name": "Test Org"},  # No credentials
        }

        result = metadata_service.get_organization_metadata("org123")

        assert result["success"] is False
        assert "credentials not found" in result["error"]

    def test_get_metadata_exception_handling(self, metadata_service, mock_firebase):
        """Test exception handling"""
        mock_firebase.db_get.side_effect = Exception("Unexpected error")

        result = metadata_service.get_organization_metadata("org123")

        assert result["success"] is False
        assert "error" in result


# =============================================================================
# get_nedarim_credentials tests
# =============================================================================
class TestGetNedarimCredentials:
    """Tests for get_nedarim_credentials method"""

    def test_get_credentials_success(
        self, metadata_service, mock_firebase, sample_metadata
    ):
        """Test successful credentials retrieval"""
        mock_firebase.db_get.return_value = {"success": True, "data": sample_metadata}

        result = metadata_service.get_nedarim_credentials("org123")

        assert result["success"] is True
        assert "credentials" in result

    def test_get_credentials_returns_mosad_id(
        self, metadata_service, mock_firebase, sample_metadata
    ):
        """Test credentials include mosad_id"""
        mock_firebase.db_get.return_value = {"success": True, "data": sample_metadata}

        result = metadata_service.get_nedarim_credentials("org123")

        assert result["credentials"]["mosad_id"] == "mosad123"

    def test_get_credentials_returns_api_valid(
        self, metadata_service, mock_firebase, sample_metadata
    ):
        """Test credentials include api_valid"""
        mock_firebase.db_get.return_value = {"success": True, "data": sample_metadata}

        result = metadata_service.get_nedarim_credentials("org123")

        assert result["credentials"]["api_valid"] == "api_key_valid_123"

    def test_get_credentials_propagates_error(self, metadata_service, mock_firebase):
        """Test error propagation from get_organization_metadata"""
        mock_firebase.db_get.return_value = {
            "success": False,
            "error": "Database error",
        }

        result = metadata_service.get_nedarim_credentials("org123")

        assert result["success"] is False


# =============================================================================
# get_print_pricing tests
# =============================================================================
class TestGetPrintPricing:
    """Tests for get_print_pricing method"""

    def test_get_pricing_success(self, metadata_service, mock_firebase):
        """Test successful pricing retrieval"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": 0.5, "colorPrice": 2.0},
        }

        result = metadata_service.get_print_pricing("org123")

        assert result["success"] is True
        assert "pricing" in result

    def test_get_pricing_values(self, metadata_service, mock_firebase):
        """Test pricing values are returned correctly"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"blackAndWhitePrice": 0.5, "colorPrice": 2.0},
        }

        result = metadata_service.get_print_pricing("org123")

        assert result["pricing"]["black_and_white_price"] == 0.5
        assert result["pricing"]["color_price"] == 2.0

    def test_get_pricing_default_values(self, metadata_service, mock_firebase):
        """Test default pricing values when not set"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"name": "Test Org"},  # Has data but no pricing fields
        }

        result = metadata_service.get_print_pricing("org123")

        assert result["success"] is True
        assert result["pricing"]["black_and_white_price"] == 1.0
        assert result["pricing"]["color_price"] == 3.0

    def test_get_pricing_firebase_failure(self, metadata_service, mock_firebase):
        """Test handling of Firebase failure"""
        mock_firebase.db_get.return_value = {
            "success": False,
            "error": "Connection failed",
        }

        result = metadata_service.get_print_pricing("org123")

        assert result["success"] is False

    def test_get_pricing_no_data(self, metadata_service, mock_firebase):
        """Test handling of missing metadata"""
        mock_firebase.db_get.return_value = {"success": True, "data": None}

        result = metadata_service.get_print_pricing("org123")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_pricing_exception_handling(self, metadata_service, mock_firebase):
        """Test exception handling"""
        mock_firebase.db_get.side_effect = Exception("Unexpected error")

        result = metadata_service.get_print_pricing("org123")

        assert result["success"] is False


# =============================================================================
# set_print_pricing tests
# =============================================================================
class TestSetPrintPricing:
    """Tests for set_print_pricing method"""

    def test_set_pricing_success(self, metadata_service, mock_firebase):
        """Test successful pricing update"""
        mock_firebase.db_update.return_value = {"success": True}

        result = metadata_service.set_print_pricing("org123", 0.75, 2.5)

        assert result["success"] is True

    def test_set_pricing_calls_firebase(self, metadata_service, mock_firebase):
        """Test Firebase is called with correct data"""
        mock_firebase.db_update.return_value = {"success": True}

        metadata_service.set_print_pricing("org123", 0.75, 2.5)

        mock_firebase.db_update.assert_called_once()
        call_args = mock_firebase.db_update.call_args
        assert "organizations/org123/metadata" in call_args[0][0]
        assert call_args[0][1]["blackAndWhitePrice"] == 0.75
        assert call_args[0][1]["colorPrice"] == 2.5

    def test_set_pricing_firebase_failure(self, metadata_service, mock_firebase):
        """Test handling of Firebase failure"""
        mock_firebase.db_update.return_value = {
            "success": False,
            "error": "Update failed",
        }

        result = metadata_service.set_print_pricing("org123", 1.0, 3.0)

        assert result["success"] is False

    def test_set_pricing_exception_handling(self, metadata_service, mock_firebase):
        """Test exception handling"""
        mock_firebase.db_update.side_effect = Exception("Unexpected error")

        result = metadata_service.set_print_pricing("org123", 1.0, 3.0)

        assert result["success"] is False

    def test_set_pricing_with_zero_values(self, metadata_service, mock_firebase):
        """Test setting zero prices"""
        mock_firebase.db_update.return_value = {"success": True}

        result = metadata_service.set_print_pricing("org123", 0.0, 0.0)

        assert result["success"] is True

    def test_set_pricing_with_high_values(self, metadata_service, mock_firebase):
        """Test setting high price values"""
        mock_firebase.db_update.return_value = {"success": True}

        result = metadata_service.set_print_pricing("org123", 10.0, 50.0)

        assert result["success"] is True
        call_args = mock_firebase.db_update.call_args
        assert call_args[0][1]["blackAndWhitePrice"] == 10.0
        assert call_args[0][1]["colorPrice"] == 50.0
