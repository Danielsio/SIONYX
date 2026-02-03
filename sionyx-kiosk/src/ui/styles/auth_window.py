"""
Styles for Unified Auth Window with sliding panels
Inspired by modern web design with vibrant gradients
"""

AUTH_WINDOW_QSS = """
    /* Main window background */
    QWidget#AuthWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #f6f5f7, stop:1 #e8e6e9);
    }

    /* Ensure all labels have no borders */
    QLabel {
        border: none;
        background: transparent;
    }

    /* Main container - holds all panels */
    #authContainer {
        background-color: #ffffff;
        border-radius: 10px;
    }

    /* Form panels (sign-in and sign-up) */
    #formPanel {
        background-color: #ffffff;
        border: none;
        border-radius: 0px;
    }

    #formTitle {
        color: #212121;
    }

    #formSubtitle {
        color: #8e8e8e;
        margin-bottom: 10px;
    }

    /* Auth inputs */
    #authInput {
        background-color: #eee;
        border: none;
        padding: 12px 15px;
        margin: 4px 0;
        border-radius: 4px;
        color: #212121;
        font-size: 13px;
    }

    #authInput:hover {
        background-color: #e5e5e5;
    }

    #authInput:focus {
        background-color: #e0e0e0;
        border: none;
    }

    #authInput::placeholder {
        color: #9e9e9e;
    }

    /* Auth buttons (sign in / sign up) */
    #authButton {
        border-radius: 20px;
        border: 1px solid #FF4B2B;
        background-color: #FF4B2B;
        color: #FFFFFF;
        font-size: 11px;
        font-weight: bold;
        padding: 12px 45px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    #authButton:hover {
        background-color: #ff3d1f;
        border: 1px solid #ff3d1f;
    }

    #authButton:pressed {
        background-color: #e6391a;
        border: 1px solid #e6391a;
    }

    #authButton:disabled {
        background-color: #ffb3a3;
        border: 1px solid #ffb3a3;
        color: #ffffff;
    }

    /* Overlay container and panels */
    #overlayContainer {
        background: transparent;
        border: none;
    }

    #overlay {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #FF4B2B, stop:1 #FF416C);
        border: none;
    }

    QWidget#overlayPanel {
        background: transparent;
        background-color: transparent;
        border: none;
        border-radius: 0px;
    }

    #overlayTitle {
        color: #FFFFFF;
        background: transparent;
        border: none;
        padding: 0px;
    }

    #overlayText {
        color: #FFFFFF;
        line-height: 24px;
        background: transparent;
        border: none;
        padding: 0px;
    }

    /* Ghost button on overlay */
    QPushButton#overlayButton {
        border-radius: 20px;
        border: 2px solid #FFFFFF;
        background-color: transparent;
        color: #FFFFFF;
        font-size: 11px;
        font-weight: bold;
        padding: 12px 45px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    QPushButton#overlayButton:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }

    QPushButton#overlayButton:pressed {
        background-color: rgba(255, 255, 255, 0.2);
    }
"""
