"""Styles for LoginWindow components.

Focused on clean, modern card, balanced spacing, and clear affordances.
Only uses Qt-supported QSS properties.
"""

LOGIN_WINDOW_QSS = """
    /* Deep blue app background for hero look */
    QWidget#LoginWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #4F8DFB, stop:1 #0F4ACB);
    }

    /* Logo + tagline */
    #appLogo { color: #FFFFFF; letter-spacing: 4px; }
    #appTagline { color: #E0E7FF; }

    /* Login card */
    #loginCard {
        background: rgba(255, 255, 255, 215);
        border: 1px solid #DDE3F0;
        border-radius: 22px;
    }

    /* Inputs already styled by base as #inputField; add slight card-specific tweaks */
    #loginCard #inputField { font-size: 14px; }

    /* Typography inside card */
    #loginTitle { color: #0F172A; }
    #loginSubtitle { color: #475569; }
    #fieldLabel { color: #334155; }
    #mutedText { color: #64748B; }

    /* Primary action button */
    #primaryButton {
        min-height: 48px;
        border-radius: 12px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #2563EB, stop:1 #1D4ED8);
        color: #FFFFFF;
        border: none;
    }
"""


