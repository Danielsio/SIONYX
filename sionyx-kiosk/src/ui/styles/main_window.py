"""
Main Window Styles - FROST Design System
Modern dark sidebar with clean navigation.
"""

MAIN_WINDOW_QSS = """
    /* ═══════════════════════════════════════════════════════════════════════
       SIDEBAR - Modern Dark Theme
       ═══════════════════════════════════════════════════════════════════════ */
    
    #modernSidebar {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #111827,
            stop:1 #0B1220
        );
        border: none;
    }

    /* ─────────────────────────────────────────────────────────────────────────
       Navigation Buttons
       ───────────────────────────────────────────────────────────────────────── */
    
    #modernNavButton {
        background: transparent;
        color: #9CA3AF;
        border: none;
        border-radius: 12px;
        text-align: right;
        padding: 14px 18px;
        margin: 2px 12px;
        font-size: 14px;
        font-weight: 500;
    }
    
    #modernNavButton:hover {
        background: rgba(99, 102, 241, 0.14);
        color: #F1F5F9;
    }
    
    #modernNavButton:checked {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(99, 102, 241, 0.28),
            stop:1 rgba(99, 102, 241, 0.10)
        );
        color: #FFFFFF;
        font-weight: 600;
        border-right: 3px solid #6366F1;
    }
    
    #modernNavButton:checked:hover {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(99, 102, 241, 0.35),
            stop:1 rgba(99, 102, 241, 0.12)
        );
    }

    /* ─────────────────────────────────────────────────────────────────────────
       Logout Button
       ───────────────────────────────────────────────────────────────────────── */
    
    #modernLogoutButton {
        background: rgba(239, 68, 68, 0.10);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.28);
        border-radius: 10px;
        padding: 12px 18px;
        margin: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }
    
    #modernLogoutButton:hover {
        background: rgba(239, 68, 68, 0.15);
        border-color: #F87171;
        color: #FCA5A5;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       CONTENT AREA
       ═══════════════════════════════════════════════════════════════════════ */
    
    #contentStack {
        background: #F4F6FB;
    }

    /* Page backgrounds */
    #homePage, #contentPage, #helpPage, #historyPage, #packagesPage {
        background: transparent;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       GLOBAL LABEL STYLING - Remove default borders
       ═══════════════════════════════════════════════════════════════════════ */
    
    QLabel {
        border: none;
        background: transparent;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       SCROLLBARS
       ═══════════════════════════════════════════════════════════════════════ */
    
    QScrollBar:vertical {
        background: transparent;
        width: 8px;
        margin: 0;
    }
    
    QScrollBar::handle:vertical {
        background: #CBD5E1;
        border-radius: 4px;
        min-height: 40px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: #94A3B8;
    }
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: none;
        border: none;
    }

    QScrollBar:horizontal {
        background: transparent;
        height: 8px;
        margin: 0;
    }
    
    QScrollBar::handle:horizontal {
        background: #CBD5E1;
        border-radius: 4px;
        min-width: 40px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background: #94A3B8;
    }
    
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: none;
        border: none;
    }

    /* ═══════════════════════════════════════════════════════════════════════
       TOOLTIPS
       ═══════════════════════════════════════════════════════════════════════ */
    
    QToolTip {
        background: #1E293B;
        color: #F1F5F9;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }
"""
