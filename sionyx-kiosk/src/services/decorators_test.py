"""
Tests for Service Decorators

Tests the decorator pattern implementation for cross-cutting concerns:
- @authenticated - authentication checks
- @log_operation - operation logging
- @handle_firebase_errors - error handling
- @service_method - composite decorator
"""

from unittest.mock import Mock

from services.decorators import (
    _format_arg,
    authenticated,
    handle_firebase_errors,
    log_operation,
    service_method,
)


# =============================================================================
# Mock Service Class for Testing
# =============================================================================


class MockService:
    """
    Mock service class that simulates BaseService.

    Has all the methods that decorators expect:
    - is_authenticated()
    - create_error_response()
    - handle_firebase_error()
    - logger
    """

    def __init__(self, is_auth: bool = True):
        self._is_authenticated = is_auth
        self.logger = Mock()

    def is_authenticated(self) -> bool:
        return self._is_authenticated

    def create_error_response(self, error: str, error_code: str = None):
        return {
            "success": False,
            "error": error,
            "error_code": error_code,
        }

    def handle_firebase_error(self, error: Exception, operation: str):
        return {
            "success": False,
            "error": str(error),
            "operation": operation,
        }


# =============================================================================
# @authenticated Tests
# =============================================================================


class TestAuthenticatedDecorator:
    """Tests for @authenticated decorator"""

    def test_allows_authenticated_user(self):
        """Authenticated users can access decorated methods"""
        service = MockService(is_auth=True)

        @authenticated
        def get_data(self):
            return {"success": True, "data": "secret"}

        result = get_data(service)

        assert result["success"] is True
        assert result["data"] == "secret"

    def test_blocks_unauthenticated_user(self):
        """Unauthenticated users get error response"""
        service = MockService(is_auth=False)

        @authenticated
        def get_data(self):
            return {"success": True, "data": "secret"}

        result = get_data(service)

        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"

    def test_preserves_function_name(self):
        """Decorator preserves original function name"""
        MockService(is_auth=True)

        @authenticated
        def my_special_function(self):
            pass

        assert my_special_function.__name__ == "my_special_function"

    def test_passes_arguments(self):
        """Arguments are passed through to wrapped function"""
        service = MockService(is_auth=True)

        @authenticated
        def get_user(self, user_id, include_details=False):
            return {"user_id": user_id, "details": include_details}

        result = get_user(service, "user123", include_details=True)

        assert result["user_id"] == "user123"
        assert result["details"] is True


# =============================================================================
# @log_operation Tests
# =============================================================================


class TestLogOperationDecorator:
    """Tests for @log_operation decorator"""

    def test_logs_function_name(self):
        """Logs the function name"""
        service = MockService()

        @log_operation
        def fetch_users(self):
            return {"success": True}

        fetch_users(service)

        # Check that logger.info was called with function name
        service.logger.info.assert_called_once()
        call_args = service.logger.info.call_args[0][0]
        assert "fetch_users" in call_args

    def test_logs_positional_arguments(self):
        """Logs positional arguments with parameter names"""
        service = MockService()

        @log_operation
        def get_user(self, user_id, org_id):
            return {"success": True}

        get_user(service, "user123", "org456")

        call_args = service.logger.info.call_args[0][0]
        assert "user_id=user123" in call_args
        assert "org_id=org456" in call_args

    def test_logs_keyword_arguments(self):
        """Logs keyword arguments"""
        service = MockService()

        @log_operation
        def search(self, query, limit=10):
            return {"success": True}

        search(service, query="test", limit=50)

        call_args = service.logger.info.call_args[0][0]
        assert "query=test" in call_args
        assert "limit=50" in call_args

    def test_returns_original_result(self):
        """Returns the original function's result"""
        service = MockService()

        @log_operation
        def get_data(self):
            return {"success": True, "data": [1, 2, 3]}

        result = get_data(service)

        assert result["success"] is True
        assert result["data"] == [1, 2, 3]


# =============================================================================
# @handle_firebase_errors Tests
# =============================================================================


class TestHandleFirebaseErrorsDecorator:
    """Tests for @handle_firebase_errors decorator"""

    def test_passes_through_on_success(self):
        """Successful execution passes through"""
        service = MockService()

        @handle_firebase_errors()
        def get_data(self):
            return {"success": True, "data": "result"}

        result = get_data(service)

        assert result["success"] is True
        assert result["data"] == "result"

    def test_catches_exception(self):
        """Exceptions are caught and handled"""
        service = MockService()

        @handle_firebase_errors()
        def failing_method(self):
            raise ValueError("Something went wrong")

        result = failing_method(service)

        assert result["success"] is False
        assert "Something went wrong" in result["error"]

    def test_uses_custom_operation_name(self):
        """Uses custom operation name in error"""
        service = MockService()

        @handle_firebase_errors("fetch user data")
        def get_user(self):
            raise Exception("Network error")

        result = get_user(service)

        assert result["operation"] == "fetch user data"

    def test_uses_function_name_when_no_custom_name(self):
        """Uses function name when no custom name provided"""
        service = MockService()

        @handle_firebase_errors()
        def load_documents(self):
            raise Exception("Error")

        result = load_documents(service)

        assert result["operation"] == "load_documents"


# =============================================================================
# @service_method (Composite) Tests
# =============================================================================


class TestServiceMethodDecorator:
    """Tests for @service_method composite decorator"""

    def test_combines_all_decorators(self):
        """Combines logging, auth, and error handling"""
        service = MockService(is_auth=True)

        @service_method("get user")
        def get_user(self, user_id):
            return {"success": True, "user_id": user_id}

        result = get_user(service, "user123")

        # Should succeed
        assert result["success"] is True
        assert result["user_id"] == "user123"

        # Should have logged
        service.logger.info.assert_called_once()

    def test_blocks_unauthenticated(self):
        """Blocks unauthenticated users"""
        service = MockService(is_auth=False)

        @service_method("get user")
        def get_user(self, user_id):
            return {"success": True}

        result = get_user(service, "user123")

        assert result["success"] is False
        assert result["error_code"] == "AUTHENTICATION_REQUIRED"

    def test_handles_errors(self):
        """Handles errors from the wrapped function"""
        service = MockService(is_auth=True)

        @service_method("get user")
        def get_user(self, user_id):
            raise Exception("Database error")

        result = get_user(service, "user123")

        assert result["success"] is False
        assert "Database error" in result["error"]
        assert result["operation"] == "get user"


# =============================================================================
# _format_arg Helper Tests
# =============================================================================


class TestFormatArg:
    """Tests for _format_arg helper function"""

    def test_formats_none(self):
        """Formats None value"""
        assert _format_arg(None) == "None"

    def test_formats_string(self):
        """Formats string value"""
        assert _format_arg("hello") == "hello"

    def test_truncates_long_string(self):
        """Truncates strings longer than max_length"""
        long_string = "a" * 100
        result = _format_arg(long_string, max_length=20)

        assert len(result) == 20
        assert result.endswith("...")

    def test_formats_number(self):
        """Formats number value"""
        assert _format_arg(42) == "42"
        assert _format_arg(3.14) == "3.14"

    def test_formats_dict(self):
        """Formats dict value (as string)"""
        result = _format_arg({"key": "value"})
        assert "key" in result


# =============================================================================
# Integration Tests
# =============================================================================


class TestDecoratorIntegration:
    """Integration tests for decorators working together"""

    def test_decorator_order_matters(self):
        """Decorators execute in correct order"""
        # Order should be: log → auth check → error handling → actual code
        service = MockService(is_auth=False)
        call_order = []

        # Manually compose to verify order
        def my_method(self):
            call_order.append("method")
            return {"success": True}

        # The auth check should happen before the method runs
        decorated = service_method()(my_method)
        result = decorated(service)

        # Method should NOT be called (blocked by auth)
        assert "method" not in call_order
        assert result["success"] is False

        # But logging should have happened
        service.logger.info.assert_called_once()

    def test_works_with_real_service_pattern(self):
        """Works with realistic service method pattern"""
        service = MockService(is_auth=True)
        service.firebase = Mock()
        service.firebase.db_get.return_value = {
            "success": True,
            "data": {"name": "Test User"},
        }

        @service_method("get user")
        def get_user(self, user_id):
            result = self.firebase.db_get(f"users/{user_id}")
            return result

        result = get_user(service, "user123")

        assert result["success"] is True
        assert result["data"]["name"] == "Test User"
        service.firebase.db_get.assert_called_once_with("users/user123")
