"""Styles for MainWindow (sidebar + content)."""

MAIN_WINDOW_QSS = """
    /* Modern Sidebar */
    #modernSidebar {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
        border-top-right-radius: 16px;
        border-bottom-right-radius: 16px;
    }

    /* User card */
    #userCard {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
    }

    /* Nav buttons - pill style when active */
    #modernNavButton {
        background-color: transparent;
        color: #6B7280;
        border: none;
        border-radius: 10px;
        text-align: left;
        padding: 10px 12px;
        font-size: 13px;
    }
    #modernNavButton:hover { background-color: #F3F4F6; color: #111827; }
    #modernNavButton:focus { border: 1px solid #2563EB; }
    #modernNavButton:checked {
        background-color: #2563EB;
        color: #FFFFFF;
        font-weight: 600;
        border: none;
    }
    #modernNavButton:checked:hover { background-color: #1D4ED8; }

    /* Logout */
    #modernLogoutButton {
        background-color: #FEE2E2;
        color: #DC2626;
        border: 1px solid #FCA5A5;
        border-radius: 8px;
        font-size: 12px;
    }
    #modernLogoutButton:hover { background-color: #FECACA; border-color: #F87171; }

    /* Content area */
    #contentStack {
        background-color: #F3F4F6;
        border-top-left-radius: 16px;
        border-bottom-left-radius: 16px;
    }

    #homePage, #contentPage { background-color: #F9FAFB; }

    /* Stat cards */
    #statCard {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
    }

    /* Action card */
    #mainActionCard {
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        min-height: 240px;
    }

    /* Start button */
    #startButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
        color: #FFFFFF; border: none; border-radius: 12px;
    }
    #startButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
    }

    /* Package cards */
    #packageCard { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 20px; }

    /* Purchase button gradient (fallback if inline not set) */
    #purchaseButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
        color: #FFFFFF; border: none; border-radius: 28px; padding: 16px 24px;
    }
    #purchaseButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1D4ED8);
    }
"""


