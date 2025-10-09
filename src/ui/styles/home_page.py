"""Styles for HomePage components."""

HOME_PAGE_QSS = """
    /* Modern home page with better contrast */
    #homePage { 
        background-color: transparent; 
    }

    /* Stat cards with bright modern styling */
    #statCard {
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 1px solid #E2E8F0 !important;
        color: #1E293B;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Action card with bright modern styling */
    #mainActionCard {
        background-color: #FFFFFF;
        border-radius: 20px;
        border: 1px solid #E2E8F0 !important;
        min-height: 240px;
        color: #1E293B;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* Start button with bright vibrant gradient */
    #startButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #1D4ED8);
        color: #FFFFFF; 
        border: none; 
        border-radius: 14px;
        font-weight: 700;
        box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.4);
    }
    #startButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1E40AF);
        box-shadow: 0 6px 20px 0 rgba(59, 130, 246, 0.6);
    }
"""


