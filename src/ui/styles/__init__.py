"""
Styles package
Contains QSS strings for each window/component to keep logic separate.
"""

from .base import BASE_QSS
from .main_window import MAIN_WINDOW_QSS
from .auth_window import AUTH_WINDOW_QSS
from .floating_timer import (
    FLOATING_TIMER_BASE_QSS,
    FLOATING_TIMER_WARNING_QSS,
    FLOATING_TIMER_CRITICAL_QSS,
)

# Expose tokens and theme builder for future component styles
from .tokens import TOKENS, get_default_tokens
from .theme import build_base_qss


