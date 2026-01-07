"""
Service Decorators - Cross-cutting concerns for service methods.

DESIGN PATTERN: Decorator
=========================
Decorators wrap functions to add behavior before/after execution.

WHY DECORATORS HERE?
- Authentication checks are needed in almost every service method
- Logging is needed everywhere
- Error handling is duplicated across all methods
- Without decorators: 6-10 lines of boilerplate per method!

HOW DECORATORS WORK:
1. A decorator is a function that takes a function and returns a new function
2. The new function wraps the original with extra behavior
3. Python's @decorator syntax is syntactic sugar for: func = decorator(func)

EXAMPLE:
    # Without decorators (repetitive)
    def get_user(self, user_id):
        self.log_operation("get_user", f"ID: {user_id}")
        auth_error = self.require_authentication()
        if auth_error:
            return auth_error
        try:
            # actual code
        except Exception as e:
            return self.handle_firebase_error(e, "get_user")

    # With decorators (clean!)
    @authenticated
    @log_operation
    @handle_firebase_errors
    def get_user(self, user_id):
        # just the actual code - no boilerplate!

USAGE NOTES:
- Decorators execute from bottom to top (closest to function first)
- All decorators assume the method belongs to a BaseService subclass
- @authenticated should be BEFORE @handle_firebase_errors (auth first)
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional

from utils.logger import get_logger


logger = get_logger(__name__)


def authenticated(func: Callable) -> Callable:
    """
    Decorator that checks authentication before running the method.

    If user is not authenticated, returns an error response immediately
    without running the wrapped function.

    REQUIRES: Method must be on a class with:
        - self.is_authenticated() -> bool
        - self.create_error_response(error, error_code) -> Dict

    Example:
        @authenticated
        def get_user_data(self, user_id):
            # This only runs if authenticated
            return self.firebase.db_get(f"users/{user_id}")
    """

    @wraps(func)  # Preserves function name, docstring, etc.
    def wrapper(self, *args, **kwargs):
        # Check if authenticated
        if not self.is_authenticated():
            return self.create_error_response(
                "נדרשת התחברות", "AUTHENTICATION_REQUIRED"
            )
        # If authenticated, call the original function
        return func(self, *args, **kwargs)

    return wrapper


def log_operation(func: Callable) -> Callable:
    """
    Decorator that logs method entry with arguments.

    Automatically logs:
    - Method name
    - Arguments (excluding 'self')
    - Marks entry into the operation

    REQUIRES: Method must be on a class with:
        - self.logger (logging instance)

    Example:
        @log_operation
        def get_document(self, doc_id):
            ...
        # Logs: "get_document: doc_id=abc123"
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Build argument string for logging
        arg_parts = []

        # Get function parameter names (skip 'self')
        import inspect

        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())[1:]  # Skip 'self'

        # Map positional args to names
        for i, arg in enumerate(args):
            if i < len(param_names):
                arg_parts.append(f"{param_names[i]}={_format_arg(arg)}")
            else:
                arg_parts.append(_format_arg(arg))

        # Add keyword args
        for key, value in kwargs.items():
            arg_parts.append(f"{key}={_format_arg(value)}")

        args_str = ", ".join(arg_parts) if arg_parts else ""

        # Log the operation
        self.logger.info(f"{func.__name__}: {args_str}")

        # Call the original function
        return func(self, *args, **kwargs)

    return wrapper


def handle_firebase_errors(operation_name: Optional[str] = None) -> Callable:
    """
    Decorator that wraps method in try/except and handles Firebase errors.

    If an exception occurs, it's caught and converted to a proper
    error response using handle_firebase_error().

    Args:
        operation_name: Optional name for error messages. If not provided,
                       uses the function name.

    REQUIRES: Method must be on a class with:
        - self.handle_firebase_error(exception, operation) -> Dict

    Example:
        @handle_firebase_errors("get document")
        def get_document(self, doc_id):
            result = self.firebase.db_get(...)
            return self.create_success_response(result)

        # OR use function name automatically:
        @handle_firebase_errors()
        def get_document(self, doc_id):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Use provided name or function name
                op_name = operation_name or func.__name__
                return self.handle_firebase_error(e, op_name)

        return wrapper

    return decorator


def _format_arg(arg: Any, max_length: int = 50) -> str:
    """
    Format an argument for logging.

    Truncates long strings and handles special types.
    """
    if arg is None:
        return "None"

    str_repr = str(arg)

    # Truncate long strings
    if len(str_repr) > max_length:
        return str_repr[: max_length - 3] + "..."

    return str_repr


# =============================================================================
# Composite Decorators
# =============================================================================
# These combine multiple decorators for common patterns


def service_method(operation_name: Optional[str] = None) -> Callable:
    """
    Composite decorator that applies all standard service method decorators.

    Combines: @log_operation + @authenticated + @handle_firebase_errors

    This is a convenience decorator for the most common pattern where you need
    all three behaviors.

    Args:
        operation_name: Optional name for error messages

    Example:
        @service_method("get user")
        def get_user(self, user_id):
            result = self.firebase.db_get(f"users/{user_id}")
            return self.create_success_response(result.get("data"))

    DECORATOR ORDER (executed bottom to top):
    1. handle_firebase_errors - catches exceptions (innermost)
    2. authenticated - checks auth
    3. log_operation - logs entry (outermost)
    """

    def decorator(func: Callable) -> Callable:
        # Apply decorators in reverse order (bottom to top)
        decorated = handle_firebase_errors(operation_name)(func)
        decorated = authenticated(decorated)
        decorated = log_operation(decorated)
        return decorated

    return decorator
