"""
Professional Logging System with Colors
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }

    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Level symbols
    SYMBOLS = {
        'DEBUG': '🔍',
        'INFO': '✓',
        'WARNING': '⚠',
        'ERROR': '✗',
        'CRITICAL': '🔥',
    }

    def format(self, record):
        """Format log record with colors"""
        # Color for level
        level_color = self.COLORS.get(record.levelname, self.RESET)
        symbol = self.SYMBOLS.get(record.levelname, '•')

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')

        # Format module name (shortened)
        module = record.name.split('.')[-1][:15]

        # Build colored output
        colored_output = (
            f"{self.DIM}{timestamp}{self.RESET} "
            f"{level_color}{self.BOLD}{symbol} {record.levelname:8}{self.RESET} "
            f"{self.DIM}│{self.RESET} "
            f"{self.BOLD}{module:15}{self.RESET} "
            f"{self.DIM}│{self.RESET} "
            f"{record.getMessage()}"
        )

        # Add exception info if present
        if record.exc_info:
            colored_output += f"\n{self.format_exception(record.exc_info)}"

        return colored_output

    def format_exception(self, exc_info):
        """Format exception with color"""
        import traceback
        tb = ''.join(traceback.format_exception(*exc_info))
        return f"{self.COLORS['ERROR']}{tb}{self.RESET}"


class FileFormatter(logging.Formatter):
    """Detailed formatter for file output (no colors)"""

    def format(self, record):
        """Format log record for file"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        output = (
            f"{timestamp} | "
            f"{record.levelname:8} | "
            f"{record.name:30} | "
            f"{record.funcName:20} | "
            f"Line {record.lineno:4} | "
            f"{record.getMessage()}"
        )

        if record.exc_info:
            import traceback
            tb = ''.join(traceback.format_exception(*record.exc_info))
            output += f"\n{tb}"

        return output


class SionyxLogger:
    """Professional logging system"""

    _initialized = False

    @classmethod
    def setup(cls, log_level=logging.INFO, log_to_file=True, enable_colors=True):
        """
        Setup professional logging system

        Args:
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Enable file logging
            enable_colors: Enable colored console output
        """
        if cls._initialized:
            return

        # Create logs directory
        log_dir = Path.home() / '.sionyx' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        # Log files
        today = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"sionyx_{today}.log"
        error_log_file = log_dir / f"sionyx_errors_{today}.log"

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture everything
        root_logger.handlers.clear()

        # Console Handler (colored, INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        if enable_colors and sys.stdout.isatty():
            console_handler.setFormatter(ColoredFormatter())
        else:
            # Fallback to simple format if no colors
            simple_format = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(simple_format)

        root_logger.addHandler(console_handler)

        # File Handler (detailed, all levels)
        if log_to_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(FileFormatter())
            root_logger.addHandler(file_handler)

            # Error File Handler (errors only)
            error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(FileFormatter())
            root_logger.addHandler(error_handler)

        cls._initialized = True

        # Log startup banner
        logger = logging.getLogger(__name__)
        logger.info("╔═══════════════════════════════════════════════════════════╗")
        logger.info("║         SIONYX - PC Time Management System                ║")
        logger.info("╚═══════════════════════════════════════════════════════════╝")
        logger.info(f"Log Level: {logging.getLevelName(log_level)}")
        if log_to_file:
            logger.info(f"Log File: {log_file}")
            logger.info(f"Error Log: {error_log_file}")
        logger.info("System Initialized")

    @classmethod
    def cleanup_old_logs(cls, days_to_keep=7):
        """Remove log files older than specified days"""
        log_dir = Path.home() / '.sionyx' / 'logs'
        if not log_dir.exists():
            return

        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days_to_keep)

        for log_file in log_dir.glob('*.log'):
            if log_file.stat().st_mtime < cutoff.timestamp():
                log_file.unlink()
                logging.getLogger(__name__).debug(f"Deleted old log: {log_file.name}")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for a module

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)

        logger.debug("Detailed debug info")
        logger.info("General information")
        logger.warning("Warning message")
        logger.error("Error occurred")
        logger.critical("Critical failure")
        logger.exception("Error with traceback")  # Use in except blocks
    """
    return logging.getLogger(name)