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
            "primary": "#3B82F6",
            "primary_hover": "#2563EB",
            "primary_pressed": "#1D4ED8",
            "success": "#10B981",
            "success_hover": "#059669",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "error_bg": "#FEF2F2",
            "text": "#0F172A",
            "text_muted": "#64748B",
            "text_subtle": "#94A3B8",
            "surface": "#FFFFFF",
            "surface_subtle": "#F8FAFC",
            "surface_alt": "#F1F5F9",
            "border": "#E2E8F0",
            "border_alt": "#CBD5E1",
            "scrollbar": "#CBD5E1",
            "scrollbar_hover": "#94A3B8",
            "selection_bg": "#3B82F6",
            "selection_text": "#FFFFFF",
            # Sidebar colors (dark mode)
            "sidebar_bg": "#1E293B",
            "sidebar_text": "#E2E8F0",
            "sidebar_text_muted": "#94A3B8",
            "sidebar_hover": "#334155",
            "sidebar_active": "#3B82F6",
            # Content background
            "content_bg": "#F8FAFC",
        },
    }


def get_dark_tokens() -> Dict[str, Dict[str, str]]:
    """Return the design tokens for the dark theme."""
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
            "primary": "#3B82F6",
            "primary_hover": "#2563EB",
            "primary_pressed": "#1D4ED8",
            "success": "#10B981",
            "success_hover": "#059669",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "error_bg": "#7F1D1D",
            "text": "#F8FAFC",
            "text_muted": "#94A3B8",
            "text_subtle": "#64748B",
            "surface": "#1E293B",
            "surface_subtle": "#334155",
            "surface_alt": "#0F172A",
            "border": "#475569",
            "border_alt": "#64748B",
            "scrollbar": "#475569",
            "scrollbar_hover": "#64748B",
            "selection_bg": "#3B82F6",
            "selection_text": "#FFFFFF",
            # Sidebar colors (dark mode)
            "sidebar_bg": "#0F172A",
            "sidebar_text": "#F1F5F9",
            "sidebar_text_muted": "#94A3B8",
            "sidebar_hover": "#1E293B",
            "sidebar_active": "#3B82F6",
            # Content background
            "content_bg": "#0F172A",
        },
    }


# Singleton-style exported tokens for convenience
TOKENS: Dict[str, Dict[str, str]] = get_default_tokens()
