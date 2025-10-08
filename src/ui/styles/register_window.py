"""Styles for RegisterWindow components.

Designed to mirror LoginWindow while accommodating a longer form.
"""

REGISTER_WINDOW_QSS = """
    /* Deep blue app background for hero look */
    QWidget#RegisterWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #4F8DFB, stop:1 #0F4ACB);
    }

    /* Register card */
    #registerCard {
        background: rgba(255, 255, 255, 215);
        border: 1px solid #DDE3F0;
        border-radius: 22px;
    }

    #registerTitle { color: #0F172A; }
    #registerSubtitle { color: #E0E7FF; }
    #fieldLabel { color: #334155; }
    #mutedText { color: #64748B; }

    #registerCard #inputField { font-size: 14px; }

    #primaryButton { min-height: 48px; border-radius: 12px; }
"""


