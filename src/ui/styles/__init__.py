"""
Styles package
Contains QSS strings for each window/component to keep logic separate.
"""

from .base import BASE_QSS
from .main_window import MAIN_WINDOW_QSS
from .auth_window import AUTH_WINDOW_QSS

# Expose tokens and theme builder for future component styles
from .tokens import TOKENS, get_default_tokens
from .theme import build_base_qss


