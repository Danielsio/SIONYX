"""
Design tokens for the desktop app theme.

These tokens power the generated QSS so we can scale consistently across
typography, color, spacing, and radii. Inspired by Fluent/Material systems.
"""

from typing import Dict


def get_default_tokens() -> Dict[str, Dict[str, str]]:
    """Return the default design tokens for the light theme."""
    return {
        "typography": {
            "font_family": "'Segoe UI'",
            "font_size_xs": "11px",
            "font_size_sm": "12px",
            "font_size_base": "13px",
            "font_size_md": "14px",
            "font_size_lg": "16px",
            "font_size_xl": "18px",
            "font_size_2xl": "24px",
            "font_size_3xl": "30px",
        },
        "radius": {
            "xs": "6px",
            "sm": "8px",
            "md": "10px",
            "lg": "12px",
            "xl": "16px",
            "xxl": "20px",
            "round": "999px",
        },
        "spacing": {
            "xs": "6px",
            "sm": "8px",
            "md": "10px",
            "lg": "12px",
            "xl": "16px",
            "2xl": "20px",
            "3xl": "24px",
        },
        "palette": {
            "primary": "#2563EB",
            "primary_hover": "#1D4ED8",
            "primary_pressed": "#1E40AF",
            "success": "#10B981",
            "success_hover": "#059669",
            "warning": "#F59E0B",
            "error": "#DC2626",
            "error_bg": "#FEF2F2",
            "text": "#111827",
            "text_muted": "#6B7280",
            "text_subtle": "#9CA3AF",
            "surface": "#FFFFFF",
            "surface_subtle": "#F9FAFB",
            "surface_alt": "#F3F4F6",
            "border": "#E5E7EB",
            "border_alt": "#CBD5E1",
            "scrollbar": "#CBD5E1",
            "scrollbar_hover": "#94A3B8",
            "selection_bg": "#1976D2",
            "selection_text": "#FFFFFF",
            "app_bg_0": "#EAF3FE",
            "app_bg_50": "#CFE6FD",
            "app_bg_100": "#B9DBFC",
        },
    }


# Singleton-style exported tokens for convenience
TOKENS: Dict[str, Dict[str, str]] = get_default_tokens()


