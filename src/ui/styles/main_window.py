"""Styles for MainWindow (sidebar + content)."""

MAIN_WINDOW_QSS = """
    /* Modern Dark Sidebar with strong contrast */
    #modernSidebar {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #1E293B,
            stop:1 #0F172A
        );
        border: none;
    }

    /* User card in dark sidebar */
    #userCard {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Nav buttons with modern styling */
    #modernNavButton {
        background-color: transparent;
        color: #94A3B8;
        border: none;
        text-align: left;
        padding: 12px 14px;
        font-size: 14px;
        font-weight: 500;
    }
    #modernNavButton:hover { 
        background-color: #334155; 
        color: #E2E8F0; 
    }
    #modernNavButton:focus { 
        border: none; 
        outline: 2px solid #3B82F6;
        outline-offset: -2px;
    }
    #modernNavButton:checked {
        background-color: #3B82F6;
        color: #FFFFFF;
        font-weight: 600;
        border: none;
    }
    #modernNavButton:checked:hover { 
        background-color: #2563EB; 
    }

    /* Logout button with better styling */
    #modernLogoutButton {
        background-color: rgba(239, 68, 68, 0.1);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.2);
        font-size: 13px;
        font-weight: 600;
    }
    #modernLogoutButton:hover { 
        background-color: rgba(239, 68, 68, 0.2); 
        border-color: #F87171;
        color: #FCA5A5;
    }

    /* Content area with sophisticated grayish background */
    #contentStack {
        background: qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 #F1F5F9,
            stop:1 #E2E8F0
        );
    }

    /* All pages with matching dark background */
    #homePage, #contentPage, #helpPage, #historyPage { 
        background-color: transparent;
    }

"""
