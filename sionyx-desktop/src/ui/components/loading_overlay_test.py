"""
Tests for Loading Overlay Component
"""

import pytest
from PyQt6.QtWidgets import QWidget

from ui.components.loading_overlay import LoadingOverlay, SpinnerWidget


class TestSpinnerWidget:
    """Tests for SpinnerWidget animation component"""

    @pytest.fixture
    def spinner(self, qapp):
        """Create SpinnerWidget instance"""
        widget = SpinnerWidget(size=48)
        yield widget
        widget.stop()

    def test_spinner_creates_with_default_size(self, qapp):
        """Test spinner creates with specified size"""
        spinner = SpinnerWidget(size=48)
        assert spinner.width() == 48
        assert spinner.height() == 48
        spinner.stop()

    def test_spinner_creates_with_custom_size(self, qapp):
        """Test spinner creates with custom size"""
        spinner = SpinnerWidget(size=64)
        assert spinner.width() == 64
        assert spinner.height() == 64
        spinner.stop()

    def test_spinner_timer_starts_automatically(self, spinner):
        """Test spinner animation timer starts on creation"""
        assert spinner._timer.isActive()

    def test_spinner_stop_stops_timer(self, spinner):
        """Test stop() stops the animation timer"""
        spinner.stop()
        assert not spinner._timer.isActive()

    def test_spinner_start_restarts_timer(self, spinner):
        """Test start() restarts the animation timer"""
        spinner.stop()
        assert not spinner._timer.isActive()
        spinner.start()
        assert spinner._timer.isActive()

    def test_spinner_rotate_updates_angle(self, spinner):
        """Test _rotate updates the angle"""
        initial_angle = spinner._angle
        spinner._rotate()
        assert spinner._angle != initial_angle


class TestLoadingOverlay:
    """Tests for LoadingOverlay component"""

    @pytest.fixture
    def parent_widget(self, qapp):
        """Create parent widget for overlay"""
        parent = QWidget()
        parent.setFixedSize(800, 600)
        yield parent
        parent.close()

    @pytest.fixture
    def overlay(self, parent_widget):
        """Create LoadingOverlay instance"""
        overlay = LoadingOverlay(parent_widget)
        yield overlay
        if overlay._spinner._timer.isActive():
            overlay._spinner.stop()

    def test_overlay_hidden_by_default(self, overlay):
        """Test overlay is hidden when created"""
        assert not overlay.isVisible()

    def test_overlay_show_with_message_shows_overlay(self, overlay, parent_widget):
        """Test show_with_message makes overlay visible"""
        parent_widget.show()
        overlay.show_with_message("טוען...")
        assert overlay.isVisible()

    def test_overlay_show_with_message_sets_text(self, overlay):
        """Test show_with_message sets the message text"""
        overlay.show_with_message("מתחבר...")
        assert overlay._message_label.text() == "מתחבר..."

    def test_overlay_show_with_message_starts_spinner(self, overlay):
        """Test show_with_message starts the spinner animation"""
        overlay.show_with_message("טוען...")
        assert overlay._spinner._timer.isActive()

    def test_overlay_hide_overlay_hides_after_animation(self, overlay, qapp):
        """Test hide_overlay hides the overlay"""
        overlay.show_with_message("טוען...")
        overlay.hide_overlay()
        # Manually trigger the animation completion
        overlay._on_fade_out_complete()
        assert not overlay.isVisible()

    def test_overlay_hide_overlay_stops_spinner(self, overlay, qapp):
        """Test hide_overlay stops the spinner"""
        overlay.show_with_message("טוען...")
        overlay.hide_overlay()
        overlay._on_fade_out_complete()
        assert not overlay._spinner._timer.isActive()

    def test_overlay_update_message_changes_text(self, overlay):
        """Test update_message changes the displayed message"""
        overlay.show_with_message("טוען...")
        overlay.update_message("אנא המתן...")
        assert overlay._message_label.text() == "אנא המתן..."

    def test_overlay_blocks_mouse_events(self, overlay):
        """Test overlay blocks mouse events when shown"""
        from PyQt6.QtCore import QEvent, QPointF, Qt
        from PyQt6.QtGui import QMouseEvent

        overlay.show_with_message("טוען...")
        # Create a mock mouse event with correct PyQt6 signature
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(overlay.rect().center()),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.mousePressEvent(event)
        assert event.isAccepted()

    def test_overlay_blocks_key_events(self, overlay):
        """Test overlay blocks key events when shown"""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QKeyEvent

        overlay.show_with_message("טוען...")
        event = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.keyPressEvent(event)
        assert event.isAccepted()

    def test_overlay_fills_parent(self, overlay, parent_widget):
        """Test overlay fills the parent widget"""
        overlay.show_with_message("טוען...")
        assert overlay.geometry() == parent_widget.rect()

    def test_overlay_hide_when_not_visible_does_nothing(self, overlay):
        """Test hide_overlay does nothing when overlay is not visible"""
        # Should not raise any errors
        overlay.hide_overlay()

    def test_overlay_default_message(self, overlay):
        """Test default loading message is Hebrew"""
        overlay.show_with_message()
        assert overlay._message_label.text() == "טוען..."

    def test_overlay_resize_event_updates_geometry(self, overlay, parent_widget):
        """Test resize event updates overlay geometry"""
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QResizeEvent

        parent_widget.show()
        overlay.show_with_message("טוען...")
        new_size = QSize(1000, 800)
        event = QResizeEvent(new_size, parent_widget.size())
        overlay.resizeEvent(event)
        # Overlay should still match parent rect
        assert overlay.geometry() == parent_widget.rect()


class TestSpinnerPaint:
    """Tests for SpinnerWidget paint functionality"""

    @pytest.fixture
    def spinner(self, qapp):
        """Create SpinnerWidget instance"""
        widget = SpinnerWidget(size=48)
        yield widget
        widget.stop()

    def test_spinner_paint_event_executes(self, spinner, qapp):
        """Test paintEvent can be called without errors"""
        from PyQt6.QtGui import QPaintEvent

        # Create a paint event for the spinner's rect
        event = QPaintEvent(spinner.rect())
        # This should execute without raising
        spinner.paintEvent(event)

    def test_spinner_paint_event_after_rotation(self, spinner, qapp):
        """Test paintEvent works after angle changes"""
        from PyQt6.QtGui import QPaintEvent

        spinner._angle = 180
        event = QPaintEvent(spinner.rect())
        spinner.paintEvent(event)
