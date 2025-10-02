from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont


class TimerOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.dragging = False
        self.offset = QPoint()

    def init_ui(self):
        # Remove window frame and make always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        # Semi-transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set size and position
        self.setFixedSize(220, 100)
        self.move(50, 50)  # Top-left corner by default

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Time label
        self.time_label = QLabel("0h 0m 0s")
        self.time_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.time_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Prints label
        self.prints_label = QLabel("Prints: 0")
        self.prints_label.setFont(QFont("Segoe UI", 12))
        self.prints_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: rgba(0, 0, 0, 180);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.prints_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.time_label)
        layout.addWidget(self.prints_label)

        self.setLayout(layout)

    def update_time(self, seconds: int):
        """Update the displayed time"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        self.time_label.setText(f"{hours}h {minutes}m {secs}s")

        # Change color based on remaining time
        if seconds < 300:  # Less than 5 minutes
            self.time_label.setStyleSheet("""
                QLabel {
                    color: #ff0000;
                    background-color: rgba(0, 0, 0, 180);
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
        elif seconds < 1800:  # Less than 30 minutes
            self.time_label.setStyleSheet("""
                QLabel {
                    color: #ffaa00;
                    background-color: rgba(0, 0, 0, 180);
                    border-radius: 10px;
                    padding: 10px;
                }
            """)

    def update_prints(self, prints: int):
        """Update the displayed print count"""
        self.prints_label.setText(f"Prints: {prints}")

    # Make window draggable
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False