"""Styles for PackagesPage components."""

PACKAGES_PAGE_QSS = """
    /* Packages page content area */
    #contentPage { 
        background-color: transparent; 
    }

    /* Package cards with bright modern styling */
    #packageCard { 
        background-color: #FFFFFF; 
        border: 1px solid #E2E8F0 !important; 
        border-radius: 24px; 
        color: #1E293B;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Purchase button with bright vibrant colors */
    #purchaseButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
        color: #FFFFFF; 
        border: none; 
        border-radius: 32px; 
        padding: 16px 24px;
        font-weight: 700;
        box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.4);
    }
    #purchaseButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
        box-shadow: 0 6px 20px 0 rgba(16, 185, 129, 0.6);
    }
    #purchaseButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #065F46);
    }
"""


