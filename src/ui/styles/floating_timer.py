"""Styles for FloatingTimer states."""

FLOATING_TIMER_BASE_QSS = """
    #timerContainer { background-color: rgba(59, 130, 246, 0.95); border: 2px solid #2563EB; border-radius: 12px; }
    #timeDisplay { color: #FFFFFF; }
    #statusLabel { color: #DBEAFE; }
    #returnButton { background-color: #FFFFFF; color: #2563EB; border: none; border-radius: 8px; }
    #returnButton:hover { background-color: #EFF6FF; }
"""

FLOATING_TIMER_WARNING_QSS = """
    #timerContainer { background-color: rgba(251, 146, 60, 0.95); border: 2px solid #EA580C; border-radius: 12px; }
    #timeDisplay { color: #FFFFFF; }
    #statusLabel { color: #FFF7ED; }
    #returnButton { background-color: #FFFFFF; color: #EA580C; border: none; border-radius: 8px; }
    #returnButton:hover { background-color: #FFF7ED; }
"""

FLOATING_TIMER_CRITICAL_QSS = """
    #timerContainer { background-color: rgba(239, 68, 68, 0.95); border: 2px solid #DC2626; border-radius: 12px; }
    #timeDisplay { color: #FFFFFF; }
    #statusLabel { color: #FEE2E2; }
    #returnButton { background-color: #FFFFFF; color: #DC2626; border: none; border-radius: 8px; }
    #returnButton:hover { background-color: #FEE2E2; }
"""


