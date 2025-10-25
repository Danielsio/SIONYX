"""
Theme builder for generating QSS from design tokens.

This keeps QSS maintainable, consistent, and scalable.
"""

from typing import Dict

from .tokens import TOKENS


def build_base_qss(tokens: Dict[str, Dict[str, str]] = TOKENS) -> str:
    t = tokens
    p = t["palette"]
    r = t["radius"]
    ty = t["typography"]

    # Global, cards, inputs, buttons, scrollbars, tooltips
    qss = f"""
    /* Global font + background */
    * {{ font-family: {ty['font_family']}; }}

    QWidget {{
        background-color: {p['surface_alt']};
    }}

    /* Card styling */
    QFrame {{
        background-color: {p['surface']};
        border-radius: {r['xl']};
        border: none;
    }}

    /* Inputs */
    #inputField {{
        padding: 14px 16px;
        border: 2px solid {p['border_alt']};
        border-radius: {r['lg']};
        background-color: #F8FAFC;
        color: {p['text']};
        font-size: {ty['font_size_base']};
        selection-background-color: {p['selection_bg']};
        selection-color: {p['selection_text']};
    }}
    #inputField:hover {{ border: 2px solid #94A3B8; background-color: {p['surface']}; }}
    #inputField:focus {{ border: 2px solid {p['primary']}; background-color: {p['surface']}; }}
    #inputField::placeholder {{ color: #94A3B8; }}

    /* Default buttons */
    QPushButton {{
        background-color: {p['surface']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: {r['md']};
        padding: 10px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background-color: #F9FAFB; }}
    QPushButton:pressed {{ background-color: #EFF1F5; }}
    QPushButton:focus {{ border: 1px solid {p['primary']}; }}
    QPushButton:disabled {{
        background-color: #E5E7EB;
        color: #9CA3AF;
        border-color: #E5E7EB;
    }}

    /* Primary button */
    #primaryButton {{
        background-color: #1976D2; /* Keep brand hue for now */
        color: {p['surface']};
        border: none;
        border-radius: {r['lg']};
        font-weight: 700;
        font-size: {ty['font_size_md']};
        letter-spacing: 0.3px;
    }}
    #primaryButton:hover {{ background-color: #1565C0; }}
    #primaryButton:pressed {{ background-color: #0D47A1; }}
    #primaryButton:disabled {{ background-color: #D1D5DB; color: #6B7280; }}

    /* Scrollbars */
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
    QScrollBar::handle:vertical {{ background: {p['scrollbar']}; border-radius: 5px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {p['scrollbar_hover']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 4px; }}
    QScrollBar::handle:horizontal {{ background: {p['scrollbar']}; border-radius: 5px; min-width: 30px; }}
    QScrollBar::handle:horizontal:hover {{ background: {p['scrollbar_hover']}; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* Tooltips */
    QToolTip {{
        color: {p['text']};
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-radius: {r['sm']};
        padding: 6px 10px;
    }}
    """
    return qss
