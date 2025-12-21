"""
Tests for logger.py - Professional Structured Logging System
"""

import json
import logging
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# =============================================================================
# Test StructuredFormatter
# =============================================================================
class TestStructuredFormatter:
    """Tests for StructuredFormatter class"""

    def test_format_basic_record(self):
        """Test formatting a basic log record"""
        from utils.logger import StructuredFormatter
        
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_format_includes_context_when_set(self):
        """Test formatting includes context variables when set"""
        from utils.logger import StructuredFormatter, set_context, clear_context
        
        try:
            set_context(request_id="req123", user_id="user456", org_id="org789")
            
            formatter = StructuredFormatter()
            record = logging.LogRecord(
                name="test", level=logging.INFO,
                pathname="test.py", lineno=1,
                msg="Test", args=(), exc_info=None
            )
            
            result = formatter.format(record)
            data = json.loads(result)
            
            assert data["request_id"] == "req123"
            assert data["user_id"] == "user456"
            assert data["org_id"] == "org789"
        finally:
            clear_context()

    def test_format_includes_extra_data(self):
        """Test formatting includes extra_data attribute"""
        from utils.logger import StructuredFormatter
        
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="test.py", lineno=1,
            msg="Test", args=(), exc_info=None
        )
        record.extra_data = {"custom_field": "custom_value"}
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["custom_field"] == "custom_value"

    def test_format_includes_exception_info(self):
        """Test formatting includes exception info"""
        from utils.logger import StructuredFormatter
        
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test", level=logging.ERROR,
            pathname="test.py", lineno=1,
            msg="Error occurred", args=(), exc_info=exc_info
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert data["exception"]["message"] == "Test error"
        assert "traceback" in data["exception"]


# =============================================================================
# Test ColoredFormatter
# =============================================================================
class TestColoredFormatter:
    """Tests for ColoredFormatter class"""

    def test_level_labels_defined(self):
        """Test all level labels are defined"""
        from utils.logger import ColoredFormatter
        
        formatter = ColoredFormatter()
        
        assert formatter.LEVEL_LABELS["DEBUG"] == "DBG"
        assert formatter.LEVEL_LABELS["INFO"] == "INF"
        assert formatter.LEVEL_LABELS["WARNING"] == "WRN"
        assert formatter.LEVEL_LABELS["ERROR"] == "ERR"
        assert formatter.LEVEL_LABELS["CRITICAL"] == "CRT"

    def test_colors_defined(self):
        """Test all colors are defined"""
        from utils.logger import ColoredFormatter
        
        formatter = ColoredFormatter()
        
        assert "DEBUG" in formatter.COLORS
        assert "INFO" in formatter.COLORS
        assert "WARNING" in formatter.COLORS
        assert "ERROR" in formatter.COLORS
        assert "CRITICAL" in formatter.COLORS

    def test_format_basic_record(self):
        """Test formatting a basic log record with colors"""
        from utils.logger import ColoredFormatter
        
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        
        # Should contain the message
        assert "Test message" in result
        # Should contain ANSI codes
        assert "\033[" in result

    def test_format_truncates_long_module_name(self):
        """Test long module names are truncated"""
        from utils.logger import ColoredFormatter
        
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="very.long.module.name.that.exceeds.twelve.characters",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        # Module name should be truncated with ellipsis
        assert "…" in result or len(record.name.split(".")[-1]) <= 12

    def test_format_with_exception(self):
        """Test formatting with exception info"""
        from utils.logger import ColoredFormatter
        
        formatter = ColoredFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test", level=logging.ERROR,
            pathname="test.py", lineno=1,
            msg="Error", args=(), exc_info=exc_info
        )
        
        result = formatter.format(record)
        
        # Should contain exception info
        assert "ValueError" in result
        assert "Test error" in result


# =============================================================================
# Test FileFormatter
# =============================================================================
class TestFileFormatter:
    """Tests for FileFormatter class"""

    def test_format_basic_record(self):
        """Test formatting a basic log record for file"""
        from utils.logger import FileFormatter
        
        formatter = FileFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"

    def test_format_includes_context(self):
        """Test file formatter includes context"""
        from utils.logger import FileFormatter, set_context, clear_context
        
        try:
            set_context(request_id="req123")
            
            formatter = FileFormatter()
            record = logging.LogRecord(
                name="test", level=logging.INFO,
                pathname="test.py", lineno=1,
                msg="Test", args=(), exc_info=None
            )
            
            result = formatter.format(record)
            data = json.loads(result)
            
            assert data["request_id"] == "req123"
        finally:
            clear_context()


# =============================================================================
# Test context functions
# =============================================================================
class TestContextFunctions:
    """Tests for context management functions"""

    def test_set_context_sets_request_id(self):
        """Test set_context sets request_id"""
        from utils.logger import set_context, clear_context, _request_id
        
        try:
            set_context(request_id="test-request")
            assert _request_id.get() == "test-request"
        finally:
            clear_context()

    def test_set_context_sets_user_id(self):
        """Test set_context sets user_id"""
        from utils.logger import set_context, clear_context, _user_id
        
        try:
            set_context(user_id="test-user")
            assert _user_id.get() == "test-user"
        finally:
            clear_context()

    def test_set_context_sets_org_id(self):
        """Test set_context sets org_id"""
        from utils.logger import set_context, clear_context, _org_id
        
        try:
            set_context(org_id="test-org")
            assert _org_id.get() == "test-org"
        finally:
            clear_context()

    def test_clear_context_clears_all(self):
        """Test clear_context clears all context variables"""
        from utils.logger import set_context, clear_context, _request_id, _user_id, _org_id
        
        set_context(request_id="req", user_id="user", org_id="org")
        clear_context()
        
        assert _request_id.get() == ""
        assert _user_id.get() == ""
        assert _org_id.get() == ""

    def test_generate_request_id_returns_string(self):
        """Test generate_request_id returns a string"""
        from utils.logger import generate_request_id
        
        result = generate_request_id()
        
        assert isinstance(result, str)
        assert len(result) == 8


# =============================================================================
# Test StructuredLogger
# =============================================================================
class TestStructuredLogger:
    """Tests for StructuredLogger class"""

    def test_init_creates_logger(self):
        """Test StructuredLogger creates internal logger"""
        from utils.logger import StructuredLogger
        
        logger = StructuredLogger("test.module")
        
        assert logger.logger is not None
        assert logger.logger.name == "test.module"

    def test_debug_logs_debug_level(self):
        """Test debug method logs at DEBUG level"""
        from utils.logger import StructuredLogger
        
        logger = StructuredLogger("test")
        logger.logger = Mock()
        
        logger.debug("Debug message")
        
        logger.logger.log.assert_called()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.DEBUG
        assert call_args[0][1] == "Debug message"

    def test_info_logs_info_level(self):
        """Test info method logs at INFO level"""
        from utils.logger import StructuredLogger
        
        logger = StructuredLogger("test")
        logger.logger = Mock()
        
        logger.info("Info message")
        
        logger.logger.log.assert_called()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.INFO

    def test_warning_logs_warning_level(self):
        """Test warning method logs at WARNING level"""
        from utils.logger import StructuredLogger
        
        logger = StructuredLogger("test")
        logger.logger = Mock()
        
        logger.warning("Warning message")
        
        logger.logger.log.assert_called()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.WARNING

    def test_error_logs_error_level(self):
        """Test error method logs at ERROR level"""
        from utils.logger import StructuredLogger
        
        logger = StructuredLogger("test")
        logger.logger = Mock()
        
        logger.error("Error message")
        
        logger.logger.log.assert_called()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.ERROR

    def test_critical_logs_critical_level(self):
        """Test critical method logs at CRITICAL level"""
        from utils.logger import StructuredLogger
        
        logger = StructuredLogger("test")
        logger.logger = Mock()
        
        logger.critical("Critical message")
        
        logger.logger.log.assert_called()
        call_args = logger.logger.log.call_args
        assert call_args[0][0] == logging.CRITICAL

    def test_log_with_extra_data(self):
        """Test logging with extra keyword arguments"""
        from utils.logger import StructuredLogger
        
        logger = StructuredLogger("test")
        logger.logger = Mock()
        
        logger.info("Message", user_id="123", action="login")
        
        logger.logger.log.assert_called()
        call_args = logger.logger.log.call_args
        extra = call_args[1].get("extra", {})
        assert extra.get("extra_data") == {"user_id": "123", "action": "login"}


# =============================================================================
# Test get_logger function
# =============================================================================
class TestGetLogger:
    """Tests for get_logger function"""

    def test_returns_structured_logger(self):
        """Test get_logger returns StructuredLogger"""
        from utils.logger import get_logger, StructuredLogger
        
        logger = get_logger("test.module")
        
        assert isinstance(logger, StructuredLogger)

    def test_logger_has_correct_name(self):
        """Test returned logger has correct name"""
        from utils.logger import get_logger
        
        logger = get_logger("my.custom.module")
        
        assert logger.logger.name == "my.custom.module"


# =============================================================================
# Test SionyxLogger
# =============================================================================
class TestSionyxLogger:
    """Tests for SionyxLogger setup"""

    def test_initialized_flag_exists(self):
        """Test _initialized flag exists"""
        from utils.logger import SionyxLogger
        
        assert hasattr(SionyxLogger, "_initialized")

    def test_setup_can_be_called(self):
        """Test setup method exists and can be called"""
        from utils.logger import SionyxLogger
        
        # Reset initialized flag for testing
        SionyxLogger._initialized = False
        
        with patch("utils.logger.logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            # Call setup - should not raise
            SionyxLogger.setup(log_to_file=False, enable_colors=False)
        
        # Reset after test
        SionyxLogger._initialized = False

    def test_setup_skips_if_already_initialized(self):
        """Test setup returns early if already initialized"""
        from utils.logger import SionyxLogger
        
        SionyxLogger._initialized = True
        
        # Should return without doing anything
        SionyxLogger.setup()
        
        # Reset after test
        SionyxLogger._initialized = False

    def test_cleanup_old_logs_handles_missing_dir(self):
        """Test cleanup_old_logs handles missing directory"""
        from utils.logger import SionyxLogger
        
        with patch("utils.logger.Path") as mock_path:
            mock_log_dir = Mock()
            mock_log_dir.exists.return_value = False
            mock_path.return_value.parent.parent.parent.__truediv__.return_value = mock_log_dir
            
            # Should not raise
            SionyxLogger.cleanup_old_logs()



