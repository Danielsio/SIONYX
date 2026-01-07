"""
Loading Overlay Component - Animated spinner with semi-transparent backdrop.
Shows loading state during API operations (login, register, logout, etc.)
"""

import math

from PyQt6.QtCore import (
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui.constants.ui_constants import (
    Animation,
    BorderRadius,
    Colors,
    Spacing,
    Typography,
)


class SpinnerWidget(QWidget):
    """
    Animated spinning arc widget.
    Draws a partial circle that rotates continuously.
    """

    def __init__(self, size: int = 48, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._angle = 0
        self._arc_length = 270  # degrees
        self._line_width = 4

        # Animation timer - rotates the spinner
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.start(16)  # ~60 FPS

    def _rotate(self):
        """Rotate the spinner by updating the angle"""
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        """Custom paint to draw the spinning arc"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate the drawing rect (inset by line width)
        margin = self._line_width
        rect = self.rect().adjusted(margin, margin, -margin, -margin)

        # Draw background circle (faded)
        bg_pen = QPen(QColor(Colors.GRAY_200))
        bg_pen.setWidth(self._line_width)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawEllipse(rect)

        # Draw the spinning arc
        arc_pen = QPen(QColor(Colors.PRIMARY))
        arc_pen.setWidth(self._line_width)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)

        # Convert to 1/16th of a degree (Qt's arc unit)
        start_angle = int(self._angle * 16)
        span_angle = int(self._arc_length * 16)
        painter.drawArc(rect, start_angle, span_angle)

    def start(self):
        """Start the spinner animation"""
        if not self._timer.isActive():
            self._timer.start(16)

    def stop(self):
        """Stop the spinner animation"""
        self._timer.stop()


class LoadingOverlay(QWidget):
    """
    Full-screen loading overlay with animated spinner and message.
    Blocks user interaction while loading.

    Usage:
        overlay = LoadingOverlay(parent_widget)
        overlay.show_with_message("מתחבר...")
        # ... do async operation ...
        overlay.hide_overlay()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._message = ""
        self._opacity_effect = None
        self._fade_animation = None
        self._build()
        self.hide()

    def _build(self):
        """Build the overlay UI"""
        # Make it fill the parent
        if self.parent():
            self.setGeometry(self.parent().rect())

        # Semi-transparent dark backdrop
        self.setStyleSheet(
            """
            LoadingOverlay {
                background: rgba(15, 23, 42, 0.6);
            }
        """
        )

        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(Spacing.LG)

        # Container card for spinner and message
        self._container = QWidget()
        self._container.setFixedSize(200, 180)
        self._container.setStyleSheet(
            f"""
            QWidget {{
                background: {Colors.WHITE};
                border-radius: {BorderRadius.XL}px;
            }}
        """
        )

        container_layout = QVBoxLayout(self._container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(Spacing.LG)
        container_layout.setContentsMargins(
            Spacing.LG, Spacing.XL, Spacing.LG, Spacing.XL
        )

        # Spinner
        self._spinner = SpinnerWidget(size=56, parent=self._container)
        container_layout.addWidget(
            self._spinner, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Message label
        self._message_label = QLabel("טוען...")
        self._message_label.setFont(
            QFont(
                Typography.FONT_FAMILY, Typography.SIZE_BASE, Typography.WEIGHT_MEDIUM
            )
        )
        self._message_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self._message_label)

        layout.addWidget(self._container)

        # Setup opacity effect for fade animations
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

    def show_with_message(self, message: str = "טוען..."):
        """
        Show the overlay with a custom message and fade-in animation.

        Args:
            message: The message to display below the spinner
        """
        self._message = message
        self._message_label.setText(message)

        # Ensure we fill parent
        if self.parent():
            self.setGeometry(self.parent().rect())

        # Raise to top
        self.raise_()
        self.show()

        # Start spinner
        self._spinner.start()

        # Fade in
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(Animation.FAST)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.start()

    def hide_overlay(self):
        """Hide the overlay with fade-out animation"""
        if not self.isVisible():
            return

        # Fade out
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(Animation.FAST)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.finished.connect(self._on_fade_out_complete)
        self._fade_animation.start()

    def _on_fade_out_complete(self):
        """Called when fade-out animation completes"""
        self._spinner.stop()
        self.hide()

    def update_message(self, message: str):
        """Update the loading message while overlay is visible"""
        self._message = message
        self._message_label.setText(message)

    def resizeEvent(self, event):
        """Handle parent resize to keep overlay covering the full area"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())

    def mousePressEvent(self, event):
        """Block all mouse clicks while loading"""
        event.accept()

    def keyPressEvent(self, event):
        """Block all key presses while loading"""
        event.accept()
