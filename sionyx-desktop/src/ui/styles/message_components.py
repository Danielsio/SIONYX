"""
Message component styles with theme support.
Provides QSS for MessageCard, MessageModal, and MessageNotification components.
"""

from .tokens import get_dark_tokens, get_default_tokens


def get_message_card_qss(tokens=None):
    """Generate QSS for MessageCard component with theme support."""
    if tokens is None:
        tokens = get_default_tokens()

    p = tokens["palette"]
    r = tokens["radius"]
    tokens["typography"]

    return f"""
        QFrame#messageCard {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface']}, stop:1 {p['surface_subtle']});
            border: 2px solid {p['border']};
            border-radius: {r['xl']};
            margin: 12px 8px;
        }}
        QFrame#messageCard:hover {{
            border: 2px solid {p['primary']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface_subtle']}, stop:1 {p['surface_alt']});
            transform: translateY(-2px);
        }}
        QFrame#messageCard:pressed {{
            transform: translateY(0px);
            border: 2px solid {p['primary_pressed']};
        }}

        QLabel {{
            color: {p['text']};
            background: transparent;
            border: none;
        }}
    """


def get_message_modal_qss(tokens=None):
    """Generate QSS for MessageModal component with theme support."""
    if tokens is None:
        tokens = get_default_tokens()

    p = tokens["palette"]
    r = tokens["radius"]
    tokens["typography"]

    return f"""
        QFrame#messageModalContainer {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface']}, stop:1 {p['surface_subtle']});
            border-radius: {r['xl']};
            border: 2px solid {p['border']};
        }}

        QFrame#messageHeader {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary']}, stop:1 {p['primary_pressed']});
            border-radius: {r['xl']} {r['xl']} 0 0;
        }}

        QFrame#messageContent {{
            background: {p['surface']};
            border: none;
        }}

        QFrame#messageFooter {{
            background: {p['surface_subtle']};
            border-top: 1px solid {p['border']};
            border-radius: 0 0 {r['xl']} {r['xl']};
        }}

        QLabel#messageText {{
            color: {p['text']};
            background: transparent;
            border: none;
            line-height: 1.7;
            font-weight: 500;
        }}

        QLabel#messageTimestamp {{
            color: {p['text_muted']};
            background: {p['surface_alt']};
            border: 1px solid {p['border']};
            border-radius: {r['lg']};
            padding: 8px 16px;
            font-weight: 600;
        }}

        QPushButton#readAllButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['success']}, stop:1 {p['success_hover']});
            color: white;
            border: none;
            border-radius: {r['xl']};
            font-weight: 800;
            font-size: 13px;
        }}
        QPushButton#readAllButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['success_hover']}, stop:1 {p['success_pressed']});
            transform: translateY(-2px);
        }}
        QPushButton#readAllButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['success_pressed']}, stop:1 #065F46);
            transform: translateY(0px);
        }}

        QPushButton#readNextButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary']}, stop:1 {p['primary_pressed']});
            color: white;
            border: none;
            border-radius: {r['xl']};
            font-weight: 800;
            font-size: 13px;
        }}
        QPushButton#readNextButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary_hover']}, stop:1 {p['primary_pressed']});
            transform: translateY(-2px);
        }}
        QPushButton#readNextButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary_pressed']}, stop:1 #1E293B);
            transform: translateY(0px);
        }}

        QPushButton#closeButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #6B7280, stop:1 #4B5563);
            color: white;
            border: none;
            border-radius: {r['xl']};
            font-weight: 800;
            font-size: 13px;
        }}
        QPushButton#closeButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #4B5563, stop:1 #374151);
            transform: translateY(-2px);
        }}
        QPushButton#closeButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #374151, stop:1 #1F2937);
            transform: translateY(0px);
        }}
    """


def get_message_notification_qss(tokens=None):
    """Generate QSS for MessageNotification component with theme support."""
    if tokens is None:
        tokens = get_default_tokens()

    p = tokens["palette"]
    r = tokens["radius"]
    tokens["typography"]

    return f"""
        QFrame#notificationContainer {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface']}, stop:1 {p['surface_subtle']});
            border: 2px solid {p['border']};
            border-radius: {r['xl']};
        }}

        QPushButton#viewButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary']}, stop:1 {p['primary_pressed']});
            color: white;
            border: none;
            border-radius: {r['lg']};
            font-weight: 800;
            font-size: 12px;
        }}
        QPushButton#viewButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary_hover']}, stop:1 {p['primary_pressed']});
            transform: translateY(-2px);
        }}
        QPushButton#viewButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary_pressed']}, stop:1 #1E293B);
            transform: translateY(0px);
        }}

        QPushButton#closeButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface_alt']}, stop:1 {p['border']});
            color: {p['text_muted']};
            border: 1px solid {p['border_alt']};
            border-radius: 18px;
            font-weight: 800;
            font-size: 14px;
        }}
        QPushButton#closeButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['border']}, stop:1 {p['border_alt']});
            color: {p['text']};
            border-color: {p['text_muted']};
        }}
        QPushButton#closeButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['border_alt']}, stop:1 {p['text_muted']});
            color: {p['surface']};
        }}
    """


def get_message_display_qss(tokens=None):
    """Generate QSS for MessageDisplay component with theme support."""
    if tokens is None:
        tokens = get_default_tokens()

    p = tokens["palette"]
    r = tokens["radius"]
    tokens["typography"]

    return f"""
        QWidget#messageDisplay {{
            background: transparent;
            border: none;
        }}

        QFrame#messageHeader {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['primary']}, stop:1 {p['primary_pressed']});
            border-radius: {r['xl']} {r['xl']} 0 0;
            border: none;
        }}

        QFrame#messagesContainer {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface']}, stop:1 {p['surface_subtle']});
            border: 2px solid {p['border']};
            border-top: none;
            border-radius: 0 0 {r['xl']} {r['xl']};
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            border-radius: 5px;
            margin: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['scrollbar']}, stop:1 {p['scrollbar_hover']});
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['scrollbar_hover']}, stop:1 {p['text_muted']});
        }}
        QScrollBar::handle:vertical:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['text_muted']}, stop:1 {p['text']});
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QLabel#noMessages {{
            color: {p['text_subtle']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface_subtle']}, stop:1 {p['surface_alt']});
            border: 2px dashed {p['border']};
            border-radius: {r['xl']};
            padding: 40px 20px;
            font-weight: 500;
        }}

        QLabel#messageCount {{
            color: {p['primary_pressed']};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['surface']}, stop:1 {p['surface_subtle']});
            border-radius: {r['xl']};
            padding: 6px 16px;
            font-weight: 800;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }}
    """


# Export theme-aware styles
MESSAGE_CARD_LIGHT_QSS = get_message_card_qss(get_default_tokens())
MESSAGE_CARD_DARK_QSS = get_message_card_qss(get_dark_tokens())

MESSAGE_MODAL_LIGHT_QSS = get_message_modal_qss(get_default_tokens())
MESSAGE_MODAL_DARK_QSS = get_message_modal_qss(get_dark_tokens())

MESSAGE_NOTIFICATION_LIGHT_QSS = get_message_notification_qss(get_default_tokens())
MESSAGE_NOTIFICATION_DARK_QSS = get_message_notification_qss(get_dark_tokens())

MESSAGE_DISPLAY_LIGHT_QSS = get_message_display_qss(get_default_tokens())
MESSAGE_DISPLAY_DARK_QSS = get_message_display_qss(get_dark_tokens())
