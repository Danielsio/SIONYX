"""
Tests for base_service.py - Base Service Classes
Tests common functionality, error handling, and response formatting.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from services.base_service import BaseService, DatabaseService


# =============================================================================
# Concrete implementations for testing abstract classes
# =============================================================================
class ConcreteBaseService(BaseService):
    """Concrete implementation for testing BaseService"""

    def get_service_name(self) -> str:
        return "TestService"


class ConcreteDatabaseService(DatabaseService):
    """Concrete implementation for testing DatabaseService"""

    def get_collection_name(self) -> str:
        return "test_collection"

    def get_service_name(self) -> str:
        return "TestDatabaseService"


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_firebase():
    """Create mock FirebaseClient"""
    firebase = Mock()
    firebase.id_token = "valid_token"
    return firebase


@pytest.fixture
def base_service(mock_firebase):
    """Create ConcreteBaseService instance"""
    with patch("services.base_service.get_logger") as mock_logger:
        mock_logger.return_value = Mock()
        return ConcreteBaseService(firebase_client=mock_firebase)


@pytest.fixture
def db_service(mock_firebase):
    """Create ConcreteDatabaseService instance"""
    with patch("services.base_service.get_logger") as mock_logger:
        mock_logger.return_value = Mock()
        return ConcreteDatabaseService(firebase_client=mock_firebase)


# =============================================================================
# BaseService initialization tests
# =============================================================================
class TestBaseServiceInit:
    """Tests for BaseService initialization"""

    def test_stores_firebase_client(self, base_service, mock_firebase):
        """Test service stores firebase client"""
        assert base_service.firebase == mock_firebase

    def test_has_logger(self, base_service):
        """Test service has logger"""
        assert hasattr(base_service, "logger")


# =============================================================================
# create_success_response tests
# =============================================================================
class TestCreateSuccessResponse:
    """Tests for create_success_response method"""

    def test_success_is_true(self, base_service):
        """Test success field is True"""
        result = base_service.create_success_response()
        assert result["success"] is True

    def test_includes_data(self, base_service):
        """Test data is included"""
        result = base_service.create_success_response(data={"key": "value"})
        assert result["data"] == {"key": "value"}

    def test_includes_message(self, base_service):
        """Test message is included"""
        result = base_service.create_success_response(message="Custom message")
        assert result["message"] == "Custom message"

    def test_default_message(self, base_service):
        """Test default message"""
        result = base_service.create_success_response()
        assert result["message"] == "Success"

    def test_includes_timestamp(self, base_service):
        """Test timestamp is included"""
        result = base_service.create_success_response()
        assert "timestamp" in result

    def test_none_data(self, base_service):
        """Test with None data"""
        result = base_service.create_success_response(data=None)
        assert result["data"] is None


# =============================================================================
# create_error_response tests
# =============================================================================
class TestCreateErrorResponse:
    """Tests for create_error_response method"""

    def test_success_is_false(self, base_service):
        """Test success field is False"""
        result = base_service.create_error_response("Error message")
        assert result["success"] is False

    def test_includes_error(self, base_service):
        """Test error message is included"""
        result = base_service.create_error_response("Something went wrong")
        assert result["error"] == "Something went wrong"

    def test_includes_error_code(self, base_service):
        """Test error code is included when provided"""
        result = base_service.create_error_response("Error", "ERR_001")
        assert result["error_code"] == "ERR_001"

    def test_no_error_code_when_none(self, base_service):
        """Test no error_code field when not provided"""
        result = base_service.create_error_response("Error")
        assert "error_code" not in result

    def test_includes_timestamp(self, base_service):
        """Test timestamp is included"""
        result = base_service.create_error_response("Error")
        assert "timestamp" in result


# =============================================================================
# handle_firebase_error tests
# =============================================================================
class TestHandleFirebaseError:
    """Tests for handle_firebase_error method"""

    def test_permission_denied_error(self, base_service):
        """Test handling permission-denied error"""
        error = Exception("permission-denied: Access not allowed")
        result = base_service.handle_firebase_error(error, "test operation")
        assert result["error_code"] == "PERMISSION_DENIED"

    def test_network_error(self, base_service):
        """Test handling network error"""
        error = Exception("network connection failed")
        result = base_service.handle_firebase_error(error, "test operation")
        assert result["error_code"] == "NETWORK_ERROR"

    def test_timeout_error(self, base_service):
        """Test handling timeout error"""
        error = Exception("Request timeout exceeded")
        result = base_service.handle_firebase_error(error, "test operation")
        assert result["error_code"] == "NETWORK_ERROR"

    def test_not_found_error(self, base_service):
        """Test handling not-found error"""
        error = Exception("Resource not-found")
        result = base_service.handle_firebase_error(error, "test operation")
        assert result["error_code"] == "NOT_FOUND"

    def test_unknown_error(self, base_service):
        """Test handling unknown error"""
        error = Exception("Some random error")
        result = base_service.handle_firebase_error(error, "test operation")
        assert result["error_code"] == "UNKNOWN_ERROR"

    def test_includes_operation_in_message(self, base_service):
        """Test error message includes operation"""
        error = Exception("Unknown error")
        result = base_service.handle_firebase_error(error, "fetching data")
        assert "fetching data" in result["error"]


# =============================================================================
# validate_required_fields tests
# =============================================================================
class TestValidateRequiredFields:
    """Tests for validate_required_fields method"""

    def test_all_fields_present(self, base_service):
        """Test validation passes when all fields present"""
        data = {"name": "John", "email": "john@test.com"}
        result = base_service.validate_required_fields(data, ["name", "email"])
        assert result is None

    def test_missing_field(self, base_service):
        """Test validation fails for missing field"""
        data = {"name": "John"}
        result = base_service.validate_required_fields(data, ["name", "email"])
        assert result is not None
        assert "email" in result

    def test_none_value(self, base_service):
        """Test validation fails for None value"""
        data = {"name": "John", "email": None}
        result = base_service.validate_required_fields(data, ["name", "email"])
        assert result is not None

    def test_empty_required_list(self, base_service):
        """Test validation passes with empty required list"""
        data = {"name": "John"}
        result = base_service.validate_required_fields(data, [])
        assert result is None

    def test_multiple_missing_fields(self, base_service):
        """Test multiple missing fields are reported"""
        data = {}
        result = base_service.validate_required_fields(data, ["name", "email", "phone"])
        assert "name" in result
        assert "email" in result
        assert "phone" in result


# =============================================================================
# safe_get tests
# =============================================================================
class TestSafeGet:
    """Tests for safe_get method"""

    def test_existing_key(self, base_service):
        """Test getting existing key"""
        data = {"name": "John"}
        result = base_service.safe_get(data, "name")
        assert result == "John"

    def test_missing_key_returns_default(self, base_service):
        """Test missing key returns default"""
        data = {"name": "John"}
        result = base_service.safe_get(data, "email", "default@test.com")
        assert result == "default@test.com"

    def test_missing_key_default_none(self, base_service):
        """Test missing key default is None"""
        data = {"name": "John"}
        result = base_service.safe_get(data, "email")
        assert result is None


# =============================================================================
# safe_int tests
# =============================================================================
class TestSafeInt:
    """Tests for safe_int method"""

    def test_valid_int(self, base_service):
        """Test converting valid int"""
        result = base_service.safe_int(42)
        assert result == 42

    def test_valid_string_int(self, base_service):
        """Test converting string int"""
        result = base_service.safe_int("42")
        assert result == 42

    def test_valid_float(self, base_service):
        """Test converting float to int"""
        result = base_service.safe_int(42.7)
        assert result == 42

    def test_none_returns_default(self, base_service):
        """Test None returns default"""
        result = base_service.safe_int(None, 10)
        assert result == 10

    def test_invalid_string_returns_default(self, base_service):
        """Test invalid string returns default"""
        result = base_service.safe_int("not a number", 5)
        assert result == 5

    def test_default_is_zero(self, base_service):
        """Test default default is 0"""
        result = base_service.safe_int(None)
        assert result == 0


# =============================================================================
# safe_float tests
# =============================================================================
class TestSafeFloat:
    """Tests for safe_float method"""

    def test_valid_float(self, base_service):
        """Test converting valid float"""
        result = base_service.safe_float(3.14)
        assert result == 3.14

    def test_valid_string_float(self, base_service):
        """Test converting string float"""
        result = base_service.safe_float("3.14")
        assert result == 3.14

    def test_valid_int(self, base_service):
        """Test converting int to float"""
        result = base_service.safe_float(42)
        assert result == 42.0

    def test_none_returns_default(self, base_service):
        """Test None returns default"""
        result = base_service.safe_float(None, 1.5)
        assert result == 1.5

    def test_invalid_string_returns_default(self, base_service):
        """Test invalid string returns default"""
        result = base_service.safe_float("not a number", 2.5)
        assert result == 2.5

    def test_default_is_zero(self, base_service):
        """Test default default is 0.0"""
        result = base_service.safe_float(None)
        assert result == 0.0


# =============================================================================
# format_timestamp tests
# =============================================================================
class TestFormatTimestamp:
    """Tests for format_timestamp method"""

    def test_returns_provided_timestamp(self, base_service):
        """Test returns provided timestamp"""
        result = base_service.format_timestamp("2024-01-15T10:00:00")
        assert result == "2024-01-15T10:00:00"

    def test_generates_timestamp_when_none(self, base_service):
        """Test generates timestamp when None provided"""
        result = base_service.format_timestamp(None)
        # Should be a valid ISO format timestamp
        assert "T" in result

    def test_generates_timestamp_when_not_provided(self, base_service):
        """Test generates timestamp when not provided"""
        result = base_service.format_timestamp()
        assert "T" in result


# =============================================================================
# is_authenticated tests
# =============================================================================
class TestIsAuthenticated:
    """Tests for is_authenticated method"""

    def test_authenticated_with_token(self, base_service, mock_firebase):
        """Test authenticated when token present"""
        mock_firebase.id_token = "valid_token"
        assert base_service.is_authenticated() is True

    def test_not_authenticated_without_token(self, base_service, mock_firebase):
        """Test not authenticated when no token"""
        mock_firebase.id_token = None
        assert base_service.is_authenticated() is False

    def test_not_authenticated_empty_token(self, base_service, mock_firebase):
        """Test not authenticated with empty token"""
        mock_firebase.id_token = ""
        assert base_service.is_authenticated() is False


# =============================================================================
# require_authentication tests
# =============================================================================
class TestRequireAuthentication:
    """Tests for require_authentication method"""

    def test_returns_none_when_authenticated(self, base_service, mock_firebase):
        """Test returns None when authenticated"""
        mock_firebase.id_token = "valid_token"
        result = base_service.require_authentication()
        assert result is None

    def test_returns_error_when_not_authenticated(self, base_service, mock_firebase):
        """Test returns error when not authenticated"""
        mock_firebase.id_token = None
        result = base_service.require_authentication()
        assert result is not None
        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"


# =============================================================================
# log_operation tests
# =============================================================================
class TestLogOperation:
    """Tests for log_operation method"""

    def test_log_operation_calls_logger(self, base_service):
        """Test log_operation calls logger.info"""
        base_service.log_operation("test_op", "details here")
        base_service.logger.info.assert_called()


# =============================================================================
# log_error tests
# =============================================================================
class TestLogError:
    """Tests for log_error method"""

    def test_log_error_calls_logger(self, base_service):
        """Test log_error calls logger.error"""
        base_service.log_error("test_op", "error message")
        base_service.logger.error.assert_called()


# =============================================================================
# DatabaseService tests
# =============================================================================
class TestDatabaseService:
    """Tests for DatabaseService class"""

    def test_initialization_sets_collection_name(self, db_service):
        """Test collection name is set on init"""
        assert db_service.collection_name == "test_collection"

    def test_get_service_name(self, db_service):
        """Test get_service_name returns service name"""
        result = db_service.get_service_name()
        assert result == "TestDatabaseService"


# =============================================================================
# DatabaseService CRUD tests
# =============================================================================
class TestDatabaseServiceCRUD:
    """Tests for DatabaseService CRUD operations"""

    def test_get_document_success(self, db_service, mock_firebase):
        """Test successful document retrieval"""
        mock_firebase.db_get.return_value = {"success": True, "data": {"name": "Test"}}
        result = db_service.get_document("doc123")
        assert result["success"] is True

    def test_get_document_requires_auth(self, db_service, mock_firebase):
        """Test get_document requires authentication"""
        mock_firebase.id_token = None
        result = db_service.get_document("doc123")
        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"

    def test_get_all_documents_success(self, db_service, mock_firebase):
        """Test successful retrieval of all documents"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"doc1": {"name": "First"}, "doc2": {"name": "Second"}},
        }
        result = db_service.get_all_documents()
        assert result["success"] is True
        assert len(result["data"]) == 2

    def test_get_all_documents_adds_ids(self, db_service, mock_firebase):
        """Test IDs are added to documents"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"doc1": {"name": "First"}},
        }
        result = db_service.get_all_documents()
        assert result["data"][0]["id"] == "doc1"

    def test_create_document_success(self, db_service, mock_firebase):
        """Test successful document creation"""
        mock_firebase.db_push.return_value = {"success": True, "name": "new_doc_id"}
        result = db_service.create_document({"name": "New Doc"})
        assert result["success"] is True

    def test_create_document_with_id(self, db_service, mock_firebase):
        """Test document creation with specific ID"""
        mock_firebase.db_set.return_value = {"success": True}
        result = db_service.create_document({"name": "New Doc"}, doc_id="custom_id")
        assert result["success"] is True

    def test_update_document_success(self, db_service, mock_firebase):
        """Test successful document update"""
        mock_firebase.db_update.return_value = {"success": True}
        result = db_service.update_document("doc123", {"name": "Updated"})
        assert result["success"] is True

    def test_delete_document_success(self, db_service, mock_firebase):
        """Test successful document deletion"""
        mock_firebase.db_delete.return_value = {"success": True}
        result = db_service.delete_document("doc123")
        assert result["success"] is True

    def test_query_documents_success(self, db_service, mock_firebase):
        """Test successful document query"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {
                "doc1": {"status": "active"},
                "doc2": {"status": "inactive"},
                "doc3": {"status": "active"},
            },
        }
        result = db_service.query_documents("status", "active")
        assert result["success"] is True
        assert len(result["data"]) == 2


# =============================================================================
# DatabaseService Error Handling tests
# =============================================================================
class TestDatabaseServiceErrorHandling:
    """Tests for DatabaseService error handling in CRUD operations"""

    @pytest.fixture
    def mock_firebase(self):
        """Create mock FirebaseClient"""
        firebase = Mock()
        firebase.id_token = "valid_token"
        return firebase

    @pytest.fixture
    def db_service(self, mock_firebase):
        """Create ConcreteDatabaseService instance"""
        with patch("services.base_service.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            return ConcreteDatabaseService(firebase_client=mock_firebase)

    def test_get_document_firebase_error(self, db_service, mock_firebase):
        """Test get_document handles Firebase errors"""
        mock_firebase.db_get.return_value = {
            "success": False,
            "error": "Database error",
        }
        result = db_service.get_document("doc123")
        assert result["success"] is False
        assert "Database error" in result["error"]

    def test_get_document_exception(self, db_service, mock_firebase):
        """Test get_document handles exceptions"""
        mock_firebase.db_get.side_effect = Exception("Unexpected error")
        result = db_service.get_document("doc123")
        assert result["success"] is False
        assert "error_code" in result

    def test_get_all_documents_firebase_error(self, db_service, mock_firebase):
        """Test get_all_documents handles Firebase errors"""
        mock_firebase.db_get.return_value = {
            "success": False,
            "error": "Database error",
        }
        result = db_service.get_all_documents()
        assert result["success"] is False

    def test_get_all_documents_exception(self, db_service, mock_firebase):
        """Test get_all_documents handles exceptions"""
        mock_firebase.db_get.side_effect = Exception("Unexpected error")
        result = db_service.get_all_documents()
        assert result["success"] is False
        assert "error_code" in result

    def test_get_all_documents_requires_auth(self, db_service, mock_firebase):
        """Test get_all_documents requires authentication"""
        mock_firebase.id_token = None
        result = db_service.get_all_documents()
        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"

    def test_create_document_firebase_error(self, db_service, mock_firebase):
        """Test create_document handles Firebase errors"""
        mock_firebase.db_push.return_value = {
            "success": False,
            "error": "Creation failed",
        }
        result = db_service.create_document({"name": "Test"})
        assert result["success"] is False

    def test_create_document_exception(self, db_service, mock_firebase):
        """Test create_document handles exceptions"""
        mock_firebase.db_push.side_effect = Exception("Unexpected error")
        result = db_service.create_document({"name": "Test"})
        assert result["success"] is False
        assert "error_code" in result

    def test_create_document_requires_auth(self, db_service, mock_firebase):
        """Test create_document requires authentication"""
        mock_firebase.id_token = None
        result = db_service.create_document({"name": "Test"})
        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"

    def test_create_document_with_id_firebase_error(self, db_service, mock_firebase):
        """Test create_document with ID handles Firebase errors"""
        mock_firebase.db_set.return_value = {"success": False, "error": "Set failed"}
        result = db_service.create_document({"name": "Test"}, doc_id="custom_id")
        assert result["success"] is False

    def test_update_document_firebase_error(self, db_service, mock_firebase):
        """Test update_document handles Firebase errors"""
        mock_firebase.db_update.return_value = {
            "success": False,
            "error": "Update failed",
        }
        result = db_service.update_document("doc123", {"name": "Updated"})
        assert result["success"] is False

    def test_update_document_exception(self, db_service, mock_firebase):
        """Test update_document handles exceptions"""
        mock_firebase.db_update.side_effect = Exception("Unexpected error")
        result = db_service.update_document("doc123", {"name": "Updated"})
        assert result["success"] is False
        assert "error_code" in result

    def test_update_document_requires_auth(self, db_service, mock_firebase):
        """Test update_document requires authentication"""
        mock_firebase.id_token = None
        result = db_service.update_document("doc123", {"name": "Updated"})
        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"

    def test_delete_document_firebase_error(self, db_service, mock_firebase):
        """Test delete_document handles Firebase errors"""
        mock_firebase.db_delete.return_value = {
            "success": False,
            "error": "Delete failed",
        }
        result = db_service.delete_document("doc123")
        assert result["success"] is False

    def test_delete_document_exception(self, db_service, mock_firebase):
        """Test delete_document handles exceptions"""
        mock_firebase.db_delete.side_effect = Exception("Unexpected error")
        result = db_service.delete_document("doc123")
        assert result["success"] is False
        assert "error_code" in result

    def test_delete_document_requires_auth(self, db_service, mock_firebase):
        """Test delete_document requires authentication"""
        mock_firebase.id_token = None
        result = db_service.delete_document("doc123")
        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"

    def test_query_documents_firebase_error(self, db_service, mock_firebase):
        """Test query_documents handles Firebase errors"""
        mock_firebase.db_get.return_value = {"success": False, "error": "Query failed"}
        result = db_service.query_documents("status", "active")
        assert result["success"] is False

    def test_query_documents_exception(self, db_service, mock_firebase):
        """Test query_documents handles exceptions"""
        mock_firebase.db_get.side_effect = Exception("Unexpected error")
        result = db_service.query_documents("status", "active")
        assert result["success"] is False
        assert "error_code" in result

    def test_query_documents_requires_auth(self, db_service, mock_firebase):
        """Test query_documents requires authentication"""
        mock_firebase.id_token = None
        result = db_service.query_documents("status", "active")
        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"


# =============================================================================
# DatabaseService Additional tests
# =============================================================================
class TestDatabaseServiceAdditional:
    """Additional tests for DatabaseService"""

    @pytest.fixture
    def mock_firebase(self):
        """Create mock FirebaseClient"""
        firebase = Mock()
        firebase.id_token = "valid_token"
        return firebase

    @pytest.fixture
    def db_service(self, mock_firebase):
        """Create ConcreteDatabaseService instance"""
        with patch("services.base_service.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            return ConcreteDatabaseService(firebase_client=mock_firebase)

    def test_get_all_documents_empty_data(self, db_service, mock_firebase):
        """Test get_all_documents with empty data"""
        mock_firebase.db_get.return_value = {"success": True, "data": {}}
        result = db_service.get_all_documents()
        assert result["success"] is True
        assert result["data"] == []

    def test_get_all_documents_null_data(self, db_service, mock_firebase):
        """Test get_all_documents with null data (empty collection)"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": None,  # Firebase returns None for empty collections
        }
        result = db_service.get_all_documents()
        # Should handle None gracefully and return empty list
        assert result["success"] is True
        assert result["data"] == []

    def test_query_documents_no_matches(self, db_service, mock_firebase):
        """Test query_documents with no matches"""
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": {"doc1": {"status": "inactive"}, "doc2": {"status": "inactive"}},
        }
        result = db_service.query_documents("status", "active")
        assert result["success"] is True
        assert len(result["data"]) == 0


# =============================================================================
# DatabaseService.get_service_name from parent class
# =============================================================================
class TestDatabaseServiceGetServiceName:
    """Tests for DatabaseService.get_service_name base implementation"""

    @pytest.fixture
    def mock_firebase(self):
        """Create mock FirebaseClient"""
        firebase = Mock()
        firebase.id_token = "valid_token"
        return firebase

    def test_get_service_name_returns_class_and_collection(self, mock_firebase):
        """Test get_service_name returns class name with collection"""

        # Create a subclass that does NOT override get_service_name
        class TestDBService(DatabaseService):
            def get_collection_name(self) -> str:
                return "my_collection"

        with patch("services.base_service.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            service = TestDBService(firebase_client=mock_firebase)

        result = service.get_service_name()
        assert "TestDBService" in result
        assert "my_collection" in result

    def test_query_documents_exception_in_filtering(self, mock_firebase):
        """Test query_documents handles exception during filtering"""
        with patch("services.base_service.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            db_service = ConcreteDatabaseService(firebase_client=mock_firebase)

        # Make db_get return success but then make get_all_documents fail
        mock_firebase.db_get.return_value = {
            "success": True,
            "data": "not a dict",  # This will fail when iterating
        }
        result = db_service.query_documents("status", "active")
        # Should handle the exception
        assert "success" in result
