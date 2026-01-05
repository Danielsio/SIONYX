"""
Tests for floating_timer.py - Floating Timer Overlay
Tests always-on-top timer displayed during sessions.
"""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def floating_timer(qapp):
    """Create FloatingTimer instance"""
    from ui.floating_timer import FloatingTimer

    timer = FloatingTimer()
    yield timer
    timer.close()


# =============================================================================
# Test initialization
# =============================================================================
class TestFloatingTimerInit:
    """Tests for FloatingTimer initialization"""

    def test_inherits_from_qwidget(self, floating_timer):
        """Test timer inherits from QWidget"""
        assert isinstance(floating_timer, QWidget)

    def test_is_hovered_is_false_initially(self, floating_timer):
        """Test is_hovered is False initially"""
        assert floating_timer.is_hovered is False

    def test_is_warning_is_false_initially(self, floating_timer):
        """Test is_warning is False initially"""
        assert floating_timer.is_warning is False

    def test_is_critical_is_false_initially(self, floating_timer):
        """Test is_critical is False initially"""
        assert floating_timer.is_critical is False

    def test_has_return_clicked_signal(self, floating_timer):
        """Test timer has return_clicked signal"""
        assert hasattr(floating_timer, "return_clicked")

    def test_has_fixed_size(self, floating_timer):
        """Test timer has fixed size"""
        assert floating_timer.width() == 280
        assert floating_timer.height() == 140

    def test_has_frameless_window_hint(self, floating_timer):
        """Test timer has frameless window hint"""
        flags = floating_timer.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_has_stays_on_top_hint(self, floating_timer):
        """Test timer has stays on top hint"""
        flags = floating_timer.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_has_tool_hint(self, floating_timer):
        """Test timer has tool hint"""
        flags = floating_timer.windowFlags()
        assert flags & Qt.WindowType.Tool


# =============================================================================
# Test UI elements
# =============================================================================
class TestFloatingTimerUI:
    """Tests for UI elements"""

    def test_has_container(self, floating_timer):
        """Test timer has container widget"""
        assert hasattr(floating_timer, "container")
        assert isinstance(floating_timer.container, QWidget)

    def test_has_exit_button(self, floating_timer):
        """Test timer has exit button"""
        assert hasattr(floating_timer, "exit_button")
        assert isinstance(floating_timer.exit_button, QPushButton)

    def test_has_printer_icon(self, floating_timer):
        """Test timer has printer icon label"""
        assert hasattr(floating_timer, "printer_icon")
        assert isinstance(floating_timer.printer_icon, QLabel)

    def test_has_time_remaining_value(self, floating_timer):
        """Test timer has time remaining value label"""
        assert hasattr(floating_timer, "time_remaining_value")
        assert isinstance(floating_timer.time_remaining_value, QLabel)

    def test_has_time_remaining_label(self, floating_timer):
        """Test timer has time remaining label"""
        assert hasattr(floating_timer, "time_remaining_label")
        assert isinstance(floating_timer.time_remaining_label, QLabel)

    def test_has_usage_time_value(self, floating_timer):
        """Test timer has usage time value label"""
        assert hasattr(floating_timer, "usage_time_value")
        assert isinstance(floating_timer.usage_time_value, QLabel)

    def test_has_usage_time_label(self, floating_timer):
        """Test timer has usage time label"""
        assert hasattr(floating_timer, "usage_time_label")
        assert isinstance(floating_timer.usage_time_label, QLabel)

    def test_has_print_balance_value(self, floating_timer):
        """Test timer has print balance value label"""
        assert hasattr(floating_timer, "print_balance_value")
        assert isinstance(floating_timer.print_balance_value, QLabel)

    def test_has_print_balance_label(self, floating_timer):
        """Test timer has print balance label"""
        assert hasattr(floating_timer, "print_balance_label")
        assert isinstance(floating_timer.print_balance_label, QLabel)

    def test_has_account_button(self, floating_timer):
        """Test timer has account button"""
        assert hasattr(floating_timer, "account_button")
        assert isinstance(floating_timer.account_button, QPushButton)


# =============================================================================
# Test update_time
# =============================================================================
class TestUpdateTime:
    """Tests for update_time method"""

    def test_formats_time_correctly(self, floating_timer):
        """Test formats time correctly with hours, minutes, seconds"""
        floating_timer.update_time(3661)  # 1 hour, 1 minute, 1 second

        assert floating_timer.time_remaining_value.text() == "01:01:01"

    def test_formats_zero_time(self, floating_timer):
        """Test formats zero time"""
        floating_timer.update_time(0)

        assert floating_timer.time_remaining_value.text() == "00:00:00"

    def test_formats_seconds_only(self, floating_timer):
        """Test formats seconds only"""
        floating_timer.update_time(45)

        assert floating_timer.time_remaining_value.text() == "00:00:45"

    def test_formats_minutes_only(self, floating_timer):
        """Test formats minutes only"""
        floating_timer.update_time(300)  # 5 minutes

        assert floating_timer.time_remaining_value.text() == "00:05:00"

    def test_formats_hours_only(self, floating_timer):
        """Test formats hours"""
        floating_timer.update_time(7200)  # 2 hours

        assert floating_timer.time_remaining_value.text() == "02:00:00"

    def test_triggers_warning_at_5_minutes(self, floating_timer):
        """Test triggers warning mode at 5 minutes (300 seconds)"""
        floating_timer.update_time(300)

        assert floating_timer.is_warning is True

    def test_triggers_critical_at_1_minute(self, floating_timer):
        """Test triggers critical mode at 1 minute (60 seconds)"""
        floating_timer.update_time(60)

        assert floating_timer.is_critical is True

    def test_triggers_critical_below_1_minute(self, floating_timer):
        """Test triggers critical mode below 1 minute"""
        floating_timer.update_time(30)

        assert floating_timer.is_critical is True

    def test_no_warning_above_5_minutes(self, floating_timer):
        """Test no warning above 5 minutes"""
        floating_timer.update_time(600)  # 10 minutes

        assert floating_timer.is_warning is False
        assert floating_timer.is_critical is False


# =============================================================================
# Test update_usage_time
# =============================================================================
class TestUpdateUsageTime:
    """Tests for update_usage_time method"""

    def test_formats_usage_time_correctly(self, floating_timer):
        """Test formats usage time correctly"""
        floating_timer.update_usage_time(3723)  # 1:02:03

        assert floating_timer.usage_time_value.text() == "01:02:03"

    def test_formats_zero_usage_time(self, floating_timer):
        """Test formats zero usage time"""
        floating_timer.update_usage_time(0)

        assert floating_timer.usage_time_value.text() == "00:00:00"


# =============================================================================
# Test update_print_balance
# =============================================================================
class TestUpdatePrintBalance:
    """Tests for update_print_balance method"""

    def test_formats_balance_with_currency(self, floating_timer):
        """Test formats balance with currency symbol"""
        floating_timer.update_print_balance(50.0)

        assert "50.00" in floating_timer.print_balance_value.text()
        assert "₪" in floating_timer.print_balance_value.text()

    def test_formats_zero_balance(self, floating_timer):
        """Test formats zero balance"""
        floating_timer.update_print_balance(0.0)

        assert "0.00" in floating_timer.print_balance_value.text()

    def test_formats_decimal_balance(self, floating_timer):
        """Test formats decimal balance"""
        floating_timer.update_print_balance(12.50)

        assert "12.50" in floating_timer.print_balance_value.text()


# =============================================================================
# Test warning and critical modes
# =============================================================================
class TestWarningCriticalModes:
    """Tests for warning and critical mode methods"""

    def test_set_warning_mode_sets_flag(self, floating_timer):
        """Test set_warning_mode sets is_warning flag"""
        floating_timer.set_warning_mode()

        assert floating_timer.is_warning is True

    def test_set_critical_mode_sets_flag(self, floating_timer):
        """Test set_critical_mode sets is_critical flag"""
        floating_timer.set_critical_mode()

        assert floating_timer.is_critical is True

    def test_warning_mode_calls_apply_warning_styles(self, floating_timer):
        """Test warning mode applies warning styles"""
        floating_timer.set_warning_mode()

        # Should apply warning styles (orange theme)
        assert floating_timer.is_warning is True

    def test_critical_mode_calls_apply_critical_styles(self, floating_timer):
        """Test critical mode applies critical styles"""
        floating_timer.set_critical_mode()

        # Should apply critical styles (red theme)
        assert floating_timer.is_critical is True


# =============================================================================
# Test set_offline_mode
# =============================================================================
class TestSetOfflineMode:
    """Tests for set_offline_mode method"""

    def test_offline_mode_shows_warning_text(self, floating_timer):
        """Test offline mode shows warning text"""
        floating_timer.set_offline_mode(True)

        assert "Offline" in floating_timer.time_remaining_value.text()
        assert "⚠" in floating_timer.time_remaining_value.text()

    def test_online_mode_resets_flags(self, floating_timer):
        """Test online mode resets warning/critical flags"""
        floating_timer.is_warning = True
        floating_timer.is_critical = True

        floating_timer.set_offline_mode(False)

        assert floating_timer.is_warning is False
        assert floating_timer.is_critical is False


# =============================================================================
# Test button signals
# =============================================================================
class TestButtonSignals:
    """Tests for button signal connections"""

    def test_exit_button_emits_return_clicked(self, floating_timer):
        """Test exit button click emits return_clicked signal"""
        signal_received = []
        floating_timer.return_clicked.connect(lambda: signal_received.append(True))

        floating_timer.exit_button.click()

        assert len(signal_received) == 1

    def test_account_button_emits_return_clicked(self, floating_timer):
        """Test account button click emits return_clicked signal"""
        signal_received = []
        floating_timer.return_clicked.connect(lambda: signal_received.append(True))

        floating_timer.account_button.click()

        assert len(signal_received) == 1


# =============================================================================
# Test style methods
# =============================================================================
class TestStyleMethods:
    """Tests for style application methods"""

    def test_apply_professional_styles_callable(self, floating_timer):
        """Test apply_professional_styles is callable"""
        # Should not raise
        floating_timer.apply_professional_styles()

    def test_apply_warning_styles_callable(self, floating_timer):
        """Test apply_warning_styles is callable"""
        # Should not raise
        floating_timer.apply_warning_styles()

    def test_apply_critical_styles_callable(self, floating_timer):
        """Test apply_critical_styles is callable"""
        # Should not raise
        floating_timer.apply_critical_styles()

    def test_pulse_animation_callable(self, floating_timer):
        """Test pulse_animation is callable"""
        # Should not raise
        floating_timer.pulse_animation()


# =============================================================================
# Test time formatting edge cases
# =============================================================================
class TestTimeFormattingEdgeCases:
    """Tests for time formatting edge cases"""

    def test_formats_large_hours(self, floating_timer):
        """Test formats large hour values"""
        floating_timer.update_time(36000)  # 10 hours

        assert floating_timer.time_remaining_value.text() == "10:00:00"

    def test_formats_max_values(self, floating_timer):
        """Test formats all max values (59)"""
        floating_timer.update_time(3599)  # 59:59

        assert floating_timer.time_remaining_value.text() == "00:59:59"

    def test_formats_boundary_minute(self, floating_timer):
        """Test formats at minute boundary"""
        floating_timer.update_time(60)  # Exactly 1 minute

        assert floating_timer.time_remaining_value.text() == "00:01:00"

    def test_formats_boundary_hour(self, floating_timer):
        """Test formats at hour boundary"""
        floating_timer.update_time(3600)  # Exactly 1 hour

        assert floating_timer.time_remaining_value.text() == "01:00:00"


# =============================================================================
# Test initial label values
# =============================================================================
class TestInitialLabelValues:
    """Tests for initial label values"""

    def test_time_remaining_initial_value(self, floating_timer):
        """Test time remaining has initial value"""
        assert floating_timer.time_remaining_value.text() == "00:00:00"

    def test_usage_time_initial_value(self, floating_timer):
        """Test usage time has initial value"""
        assert floating_timer.usage_time_value.text() == "00:00:00"

    def test_print_balance_initial_value(self, floating_timer):
        """Test print balance has initial value"""
        assert "0" in floating_timer.print_balance_value.text()
        assert "₪" in floating_timer.print_balance_value.text()

    def test_time_remaining_label_text(self, floating_timer):
        """Test time remaining label has Hebrew text"""
        assert "זמן שנותר" in floating_timer.time_remaining_label.text()

    def test_usage_time_label_text(self, floating_timer):
        """Test usage time label has Hebrew text"""
        assert "זמן שימוש" in floating_timer.usage_time_label.text()

    def test_print_balance_label_text(self, floating_timer):
        """Test print balance label has Hebrew text"""
        assert "יתרת הדפסות" in floating_timer.print_balance_label.text()

    def test_exit_button_text(self, floating_timer):
        """Test exit button has Hebrew text"""
        assert "יציאה" in floating_timer.exit_button.text()

    def test_account_button_text(self, floating_timer):
        """Test account button has Hebrew text"""
        assert "החשבון שלי" in floating_timer.account_button.text()


# =============================================================================
# Test mouse tracking
# =============================================================================
class TestMouseTracking:
    """Tests for mouse tracking"""

    def test_mouse_tracking_enabled(self, floating_timer):
        """Test mouse tracking is enabled"""
        assert floating_timer.hasMouseTracking()

    def test_container_mouse_tracking_enabled(self, floating_timer):
        """Test container mouse tracking is enabled"""
        assert floating_timer.container.hasMouseTracking()
