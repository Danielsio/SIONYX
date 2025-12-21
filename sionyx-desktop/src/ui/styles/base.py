"""Base/global QSS shared across the app.

Now generated from design tokens via the theme builder to ensure consistency
and scalability across the UI.
"""

from .theme import build_base_qss

# Re-export Colors and Spacing from ui_constants for backwards compatibility
from ui.constants.ui_constants import Colors, Spacing

BASE_QSS = build_base_qss()

__all__ = ["BASE_QSS", "Colors", "Spacing"]
