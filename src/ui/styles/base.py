"""Base/global QSS shared across the app.

Now generated from design tokens via the theme builder to ensure consistency
and scalability across the UI.
"""

from .theme import build_base_qss


BASE_QSS = build_base_qss()
