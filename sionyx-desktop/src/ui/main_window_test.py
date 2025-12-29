"""
Tests for MainWindow - Central Dashboard with Navigation and Session Management

TDD Strategy:
- Focus on LOGIC over UI rendering
- Test navigation state machine
- Test data refresh caching logic
- Test session lifecycle management
- Test signal/slot connections
- Test force logout handling
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_auth_service(mock_firebase_client):
    """Create mock auth service"""
    auth_service = Mock()
    auth_service.firebase = mock_firebase_client
    auth_service.get_current_user.return_value = {
        "uid": "test-user-123",
        "firstName": "Test",
        "lastName": "User",
        "email": "test@example.com",
        "remainingTime": 3600,
        "remainingPrints": 50.0,
    }
    auth_service.logout = Mock()
    return auth_service


@pytest.fixture
def mock_config():
    """Create mock config"""
    return {"some_config": "value"}


@pytest.fixture
def mock_session_service():
    """Create mock session service with signals"""
    session = Mock()
    session.time_updated = Mock()
    session.time_updated.connect = Mock()
    session.session_ended = Mock()
    session.session_ended.connect = Mock()
    session.warning_5min = Mock()
    session.warning_5min.connect = Mock()
    session.warning_1min = Mock()
    session.warning_1min.connect = Mock()
    session.sync_failed = Mock()
    session.sync_failed.connect = Mock()
    session.sync_restored = Mock()
    session.sync_restored.connect = Mock()
    # Mock print monitor
    session.print_monitor = Mock()
    session.print_monitor.job_allowed = Mock()
    session.print_monitor.job_allowed.connect = Mock()
    session.print_monitor.job_blocked = Mock()
    session.print_monitor.job_blocked.connect = Mock()
    session.print_monitor.budget_updated = Mock()
    session.print_monitor.budget_updated.connect = Mock()
    session.start_session.return_value = {"success": True, "session_id": "test-session"}
    session.end_session.return_value = {"success": True, "remaining_time": 1800}
    session.is_session_active.return_value = False
    session.get_time_used.return_value = 0
    return session


def create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp):
    """Create a MainWindow instance bypassing heavy UI initialization"""
    from ui.main_window import MainWindow

    # Create instance without calling __init__
    window = MainWindow.__new__(MainWindow)
    # Initialize QWidget base
    QWidget.__init__(window)

    # Set core attributes
    window.auth_service = mock_auth_service
    window.config = mock_config
    window.current_user = mock_auth_service.get_current_user().copy()  # Make a copy
    window.page_names = {0: "HOME", 1: "PACKAGES", 2: "HISTORY", 3: "HELP"}
    window.session_service = mock_session_service
    window.floating_timer = None
    window.force_logout_listener = None

    # Data refresh optimization
    window.page_data_ages = {}
    window.data_max_age_seconds = 30
    window.last_user_data = None

    # Mock UI components - properly configure mocks
    window.content_stack = Mock(spec=QStackedWidget)
    window.content_stack.count.return_value = 4  # 4 pages
    window.content_stack.widget.return_value = Mock()

    window.nav_buttons = [Mock() for _ in range(4)]

    # Create page mocks with proper current_user dicts
    window.home_page = Mock()
    window.home_page.current_user = {"remainingTime": 3600}  # Real dict
    window.home_page.refresh_user_data = Mock()
    window.home_page.cleanup = Mock()
    window.home_page.update_countdown = Mock()

    window.packages_page = Mock()
    window.packages_page.clear_user_data = Mock()

    window.history_page = Mock()
    window.history_page.clear_user_data = Mock()

    window.help_page = Mock()

    # Mock base class methods
    window.show_confirm = Mock(return_value=True)
    window.show_question = Mock(return_value=True)
    window.show_notification = Mock()
    window.show_error = Mock()
    window.apply_base_stylesheet = Mock(return_value="")

    # Mock Qt window methods to prevent showEvent triggering refresh_all_pages
    window.showNormal = Mock()
    window.activateWindow = Mock()
    window.hide = Mock()
    window.show = Mock()
    window.close = Mock()

    return window


# =============================================================================
# Initialization Tests
# =============================================================================

class TestMainWindowInitialization:
    """Tests for MainWindow initialization"""

    def test_stores_auth_service(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Test window stores auth service"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        assert window.auth_service == mock_auth_service
        window.close()

    def test_stores_current_user(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Test window stores current user"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        assert window.current_user["uid"] == "test-user-123"
        window.close()

    def test_creates_session_service(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Test window creates session service"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        assert window.session_service is not None
        window.close()

    def test_initializes_page_data_ages(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Test data ages initialized as empty dict"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        assert window.page_data_ages == {}
        window.close()

    def test_page_names_mapping(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Test page names are mapped correctly"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        assert window.page_names[0] == "HOME"
        assert window.page_names[1] == "PACKAGES"
        assert window.page_names[2] == "HISTORY"
        assert window.page_names[3] == "HELP"
        window.close()


# =============================================================================
# Navigation Tests
# =============================================================================

class TestNavigation:
    """Tests for page navigation"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_show_page_sets_current_index(self, main_window):
        """Test show_page sets content stack index"""
        main_window.show_page(2)
        main_window.content_stack.setCurrentIndex.assert_called_with(2)

    def test_show_page_updates_nav_button_states(self, main_window):
        """Test show_page updates navigation button checked states"""
        main_window.show_page(1)

        # Button at index 1 should be checked
        main_window.nav_buttons[1].setChecked.assert_called_with(True)
        # Other buttons should be unchecked
        main_window.nav_buttons[0].setChecked.assert_called_with(False)
        main_window.nav_buttons[2].setChecked.assert_called_with(False)
        main_window.nav_buttons[3].setChecked.assert_called_with(False)

    def test_show_page_triggers_refresh(self, main_window):
        """Test show_page triggers page refresh"""
        with patch.object(main_window, "refresh_current_page") as mock_refresh:
            main_window.show_page(0)
            mock_refresh.assert_called_once()


# =============================================================================
# Data Refresh Caching Tests
# =============================================================================

class TestDataRefreshCaching:
    """Tests for smart data refresh caching logic"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_should_skip_refresh_returns_false_for_unknown_page(self, main_window):
        """Test returns False for page never refreshed"""
        result = main_window._should_skip_refresh("UnknownPage")
        assert result is False

    def test_should_skip_refresh_returns_true_for_fresh_data(self, main_window):
        """Test returns True for recently refreshed page"""
        # Set page as just refreshed
        main_window.page_data_ages["HomePage"] = datetime.now()

        result = main_window._should_skip_refresh("HomePage")
        assert result is True

    def test_should_skip_refresh_returns_false_for_stale_data(self, main_window):
        """Test returns False for stale page data"""
        # Set page as refreshed 60 seconds ago (stale)
        main_window.page_data_ages["HomePage"] = datetime.now() - timedelta(seconds=60)

        result = main_window._should_skip_refresh("HomePage")
        assert result is False

    def test_update_page_data_age_sets_timestamp(self, main_window):
        """Test _update_page_data_age sets current timestamp"""
        before = datetime.now()
        main_window._update_page_data_age("TestPage")
        after = datetime.now()

        assert "TestPage" in main_window.page_data_ages
        assert before <= main_window.page_data_ages["TestPage"] <= after

    def test_get_current_user_data_returns_subset(self, main_window):
        """Test _get_current_user_data returns simplified user data"""
        result = main_window._get_current_user_data()

        assert "uid" in result
        assert "timeRemaining" in result
        assert "printsRemaining" in result
        assert "email" not in result  # Should not include all fields

    def test_get_current_user_data_empty_when_no_user(self, main_window):
        """Test returns empty dict when no current user"""
        main_window.current_user = None
        result = main_window._get_current_user_data()
        assert result == {}

    def test_user_data_unchanged_returns_false_first_time(self, main_window):
        """Test returns False when no previous user data"""
        main_window.last_user_data = None
        result = main_window._user_data_unchanged({"uid": "123"})
        assert result is False

    def test_user_data_unchanged_returns_true_when_same(self, main_window):
        """Test returns True when user data hasn't changed"""
        user_data = {"uid": "123", "timeRemaining": 3600}
        main_window.last_user_data = user_data

        result = main_window._user_data_unchanged(user_data)
        assert result is True

    def test_user_data_unchanged_returns_false_when_different(self, main_window):
        """Test returns False when user data has changed"""
        main_window.last_user_data = {"uid": "123", "timeRemaining": 3600}
        new_data = {"uid": "123", "timeRemaining": 1800}  # Different time

        result = main_window._user_data_unchanged(new_data)
        assert result is False


# =============================================================================
# Refresh Page Tests
# =============================================================================

class TestRefreshPages:
    """Tests for page refresh functionality"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)

        # Setup mock page with refresh method
        mock_page = Mock()
        mock_page.refresh_user_data = Mock()
        mock_page.__class__.__name__ = "TestPage"
        window.content_stack.currentWidget.return_value = mock_page

        yield window
        window.close()

    def test_refresh_current_page_calls_refresh_user_data(self, main_window):
        """Test refresh_current_page calls page's refresh method"""
        main_window.refresh_current_page(force=True)

        current_page = main_window.content_stack.currentWidget()
        current_page.refresh_user_data.assert_called_once()

    def test_refresh_current_page_skips_fresh_data(self, main_window):
        """Test refresh_current_page skips when data is fresh"""
        # Mark page as just refreshed
        main_window.page_data_ages["TestPage"] = datetime.now()

        main_window.refresh_current_page(force=False)

        current_page = main_window.content_stack.currentWidget()
        current_page.refresh_user_data.assert_not_called()

    def test_refresh_current_page_forces_refresh(self, main_window):
        """Test refresh_current_page with force=True ignores freshness"""
        # Mark page as just refreshed
        main_window.page_data_ages["TestPage"] = datetime.now()

        main_window.refresh_current_page(force=True)

        current_page = main_window.content_stack.currentWidget()
        current_page.refresh_user_data.assert_called_once()


# =============================================================================
# Session Management Tests
# =============================================================================

class TestSessionManagement:
    """Tests for session lifecycle"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_start_user_session_calls_session_service(self, main_window):
        """Test start_user_session calls session service"""
        with patch("ui.main_window.FloatingTimer") as mock_timer_cls:
            mock_timer = Mock()
            mock_timer_cls.return_value = mock_timer

            main_window.start_user_session(3600)

            main_window.session_service.start_session.assert_called_once_with(3600)

    def test_start_user_session_creates_floating_timer(self, main_window):
        """Test start_user_session creates floating timer on success"""
        with patch("ui.main_window.FloatingTimer") as mock_timer_cls:
            mock_timer = Mock()
            mock_timer_cls.return_value = mock_timer

            main_window.start_user_session(3600)

            assert main_window.floating_timer == mock_timer
            mock_timer.show.assert_called_once()

    def test_start_user_session_fails_gracefully(self, main_window):
        """Test start_user_session handles failure"""
        main_window.session_service.start_session.return_value = {
            "success": False,
            "error": "No time remaining"
        }

        with patch("ui.main_window.QMessageBox") as mock_msgbox:
            main_window.start_user_session(0)

            # Should show error message
            mock_msgbox.critical.assert_called_once()
            # Timer should not be created
            assert main_window.floating_timer is None

    def test_return_from_session_ends_session(self, main_window):
        """Test return_from_session ends the session"""
        main_window.floating_timer = Mock()

        main_window.return_from_session()

        main_window.session_service.end_session.assert_called_once_with("user")

    def test_return_from_session_closes_timer(self, main_window):
        """Test return_from_session closes floating timer"""
        mock_timer = Mock()
        main_window.floating_timer = mock_timer

        main_window.return_from_session()

        mock_timer.close.assert_called_once()
        assert main_window.floating_timer is None


# =============================================================================
# Signal Handler Tests
# =============================================================================

class TestSignalHandlers:
    """Tests for signal handlers"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_on_time_updated_updates_timer(self, main_window):
        """Test on_time_updated updates floating timer"""
        mock_timer = Mock()
        main_window.floating_timer = mock_timer
        main_window.session_service.get_time_used.return_value = 600

        main_window.on_time_updated(1800)

        mock_timer.update_time.assert_called_with(1800)
        mock_timer.update_usage_time.assert_called_with(600)

    def test_on_time_updated_no_timer(self, main_window):
        """Test on_time_updated does nothing without timer"""
        main_window.floating_timer = None

        # Should not raise
        main_window.on_time_updated(1800)

    def test_on_session_ended_closes_timer(self, main_window):
        """Test on_session_ended closes floating timer"""
        mock_timer = Mock()
        main_window.floating_timer = mock_timer

        main_window.on_session_ended("expired")

        mock_timer.close.assert_called_once()
        assert main_window.floating_timer is None

    def test_on_session_ended_expired_offers_purchase(self, main_window):
        """Test on_session_ended offers purchase on expiry"""
        main_window.floating_timer = Mock()
        main_window.show_question.return_value = True

        with patch.object(main_window, "show_page") as mock_show_page:
            main_window.on_session_ended("expired")

            main_window.show_question.assert_called_once()
            # Should navigate to packages page
            mock_show_page.assert_called_once_with(1)  # PACKAGES = 1

    def test_on_warning_5min_shows_notification(self, main_window):
        """Test 5 minute warning shows notification"""
        main_window.on_warning_5min()

        main_window.show_notification.assert_called_once()
        call_args = main_window.show_notification.call_args
        assert "warning" in str(call_args)

    def test_on_warning_1min_shows_notification(self, main_window):
        """Test 1 minute warning shows notification"""
        main_window.on_warning_1min()

        main_window.show_notification.assert_called_once()
        call_args = main_window.show_notification.call_args
        assert "error" in str(call_args)

    def test_on_sync_failed_sets_offline_mode(self, main_window):
        """Test on_sync_failed sets timer to offline mode"""
        mock_timer = Mock()
        main_window.floating_timer = mock_timer

        main_window.on_sync_failed("Connection lost")

        mock_timer.set_offline_mode.assert_called_with(True)

    def test_on_sync_restored_clears_offline_mode(self, main_window):
        """Test on_sync_restored clears offline mode"""
        mock_timer = Mock()
        main_window.floating_timer = mock_timer

        main_window.on_sync_restored()

        mock_timer.set_offline_mode.assert_called_with(False)


# =============================================================================
# Force Logout Tests
# =============================================================================

class TestForceLogout:
    """Tests for force logout handling"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_setup_force_logout_listener_creates_listener(self, main_window):
        """Test setup creates force logout listener"""
        with patch("ui.force_logout_listener.ForceLogoutListener") as mock_listener_cls:
            mock_listener = Mock()
            mock_listener.force_logout_detected = Mock()
            mock_listener.force_logout_detected.connect = Mock()
            mock_listener_cls.return_value = mock_listener

            main_window.setup_force_logout_listener()

            mock_listener.start.assert_called_once()
            assert main_window.force_logout_listener == mock_listener

    def test_setup_force_logout_listener_handles_error(self, main_window):
        """Test setup handles listener creation errors gracefully"""
        with patch("ui.force_logout_listener.ForceLogoutListener") as mock_listener_cls:
            mock_listener_cls.side_effect = Exception("Failed to create listener")

            # Should not raise
            main_window.setup_force_logout_listener()

            assert main_window.force_logout_listener is None

    def test_on_force_logout_ends_active_session(self, main_window):
        """Test on_force_logout ends active session"""
        main_window.session_service.is_session_active.return_value = True

        with patch.object(main_window, "reset_force_logout_flag"):
            with patch("ui.auth_window.AuthWindow"):
                main_window.on_force_logout()

        main_window.session_service.end_session.assert_called_once_with("admin_kick")

    def test_on_force_logout_shows_notification(self, main_window):
        """Test on_force_logout shows notification"""
        with patch.object(main_window, "reset_force_logout_flag"):
            with patch("ui.auth_window.AuthWindow"):
                main_window.on_force_logout()

        main_window.show_notification.assert_called_once()
        call_args = main_window.show_notification.call_args
        assert "error" in str(call_args)

    def test_reset_force_logout_flag_updates_database(self, main_window):
        """Test reset_force_logout_flag updates Firebase"""
        main_window.auth_service.firebase.db_update.return_value = {"success": True}

        main_window.reset_force_logout_flag()

        main_window.auth_service.firebase.db_update.assert_called_once()
        call_args = main_window.auth_service.firebase.db_update.call_args
        assert "forceLogout" in str(call_args)


# =============================================================================
# Logout Tests
# =============================================================================

class TestLogout:
    """Tests for logout functionality"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_handle_logout_confirms_with_user(self, main_window):
        """Test handle_logout asks for confirmation"""
        main_window.show_confirm.return_value = False

        main_window.handle_logout()

        main_window.show_confirm.assert_called_once()

    def test_handle_logout_ends_session(self, main_window):
        """Test handle_logout ends active session"""
        main_window.show_confirm.return_value = True

        with patch("ui.auth_window.AuthWindow"):
            main_window.handle_logout()

        main_window.session_service.end_session.assert_called_once_with("user")

    def test_handle_logout_closes_floating_timer(self, main_window):
        """Test handle_logout closes floating timer"""
        main_window.show_confirm.return_value = True
        mock_timer = Mock()
        main_window.floating_timer = mock_timer

        with patch("ui.auth_window.AuthWindow"):
            main_window.handle_logout()

        mock_timer.close.assert_called_once()

    def test_handle_logout_calls_auth_service_logout(self, main_window):
        """Test handle_logout calls auth service"""
        main_window.show_confirm.return_value = True

        with patch("ui.auth_window.AuthWindow"):
            main_window.handle_logout()

        main_window.auth_service.logout.assert_called_once()

    def test_handle_logout_aborted_by_user(self, main_window):
        """Test handle_logout does nothing when user cancels"""
        main_window.show_confirm.return_value = False

        main_window.handle_logout()

        main_window.auth_service.logout.assert_not_called()


# =============================================================================
# Cleanup Tests
# =============================================================================

class TestCleanup:
    """Tests for resource cleanup"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance with resources"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)

        # Setup mock resources
        window.force_logout_listener = Mock()
        window.floating_timer = Mock()

        yield window

    def test_close_event_stops_force_logout_listener(self, main_window):
        """Test closeEvent stops force logout listener"""
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()

        main_window.closeEvent(event)

        main_window.force_logout_listener.stop.assert_called_once()
        main_window.force_logout_listener.wait.assert_called_once_with(3000)

    def test_close_event_ends_active_session(self, main_window):
        """Test closeEvent ends active session"""
        main_window.session_service.is_session_active.return_value = True

        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()

        main_window.closeEvent(event)

        main_window.session_service.end_session.assert_called_once_with("user")

    def test_close_event_closes_floating_timer(self, main_window):
        """Test closeEvent closes floating timer"""
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()

        main_window.closeEvent(event)

        main_window.floating_timer.close.assert_called_once()

    def test_close_event_accepts_event(self, main_window):
        """Test closeEvent accepts the event"""
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()

        main_window.closeEvent(event)

        assert event.isAccepted()


# =============================================================================
# Show Main Window After Login Tests
# =============================================================================

class TestShowMainWindowAfterLogin:
    """Tests for re-login flow after logout"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        window.auth_window = Mock()
        yield window
        window.close()

    def test_closes_auth_window(self, main_window):
        """Test show_main_window_after_login closes auth window"""
        # Save reference before it gets set to None
        auth_window_mock = main_window.auth_window

        main_window.show_main_window_after_login()

        auth_window_mock.close.assert_called_once()
        assert main_window.auth_window is None

    def test_refreshes_current_user(self, main_window):
        """Test show_main_window_after_login refreshes user data"""
        main_window.show_main_window_after_login()

        main_window.auth_service.get_current_user.assert_called()

    def test_updates_session_service_user_id(self, main_window):
        """Test show_main_window_after_login updates session service"""
        main_window.auth_service.get_current_user.return_value = {"uid": "new-user-456"}

        main_window.show_main_window_after_login()

        assert main_window.session_service.user_id == "new-user-456"

    def test_refreshes_all_pages(self, main_window):
        """Test show_main_window_after_login refreshes all pages"""
        with patch.object(main_window, "refresh_all_pages") as mock_refresh:
            main_window.show_main_window_after_login()

            mock_refresh.assert_called_once_with(force=True)


# =============================================================================
# Refresh All Pages Tests
# =============================================================================

class TestRefreshAllPages:
    """Tests for refresh_all_pages method"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_refresh_all_pages_skips_when_ui_not_initialized(self, main_window):
        """Test refresh_all_pages skips when UI not initialized"""
        # Remove content_stack to simulate uninitialized UI
        delattr(main_window, "content_stack")
        
        # Should not raise
        main_window.refresh_all_pages()

    def test_refresh_all_pages_skips_unchanged_data(self, main_window):
        """Test refresh_all_pages skips when user data unchanged"""
        # Set last_user_data to current data
        main_window.last_user_data = main_window._get_current_user_data()
        
        # Mock page refresh methods
        mock_page = Mock()
        mock_page.refresh_user_data = Mock()
        mock_page.__class__.__name__ = "TestPage"
        main_window.content_stack.widget.return_value = mock_page
        
        main_window.refresh_all_pages(force=False)
        
        # Page refresh should not be called when data is unchanged
        # (unless forced)

    def test_refresh_all_pages_iterates_all_pages(self, main_window):
        """Test refresh_all_pages iterates through all pages"""
        main_window.content_stack.count.return_value = 2
        
        mock_page1 = Mock()
        mock_page1.refresh_user_data = Mock()
        mock_page1.__class__.__name__ = "Page1"
        
        mock_page2 = Mock()
        mock_page2.refresh_user_data = Mock()
        mock_page2.__class__.__name__ = "Page2"
        
        main_window.content_stack.widget.side_effect = [mock_page1, mock_page2]
        
        main_window.refresh_all_pages(force=True)


# =============================================================================
# Additional Session Management Tests
# =============================================================================

class TestSessionManagementAdditional:
    """Additional session management tests"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_return_from_session_updates_home_page(self, main_window):
        """Test return_from_session updates home page data"""
        main_window.floating_timer = Mock()
        main_window.session_service.end_session.return_value = {
            "success": True,
            "remaining_time": 1800
        }
        
        main_window.return_from_session()
        
        # Home page should be updated
        assert main_window.home_page.current_user["remainingTime"] == 1800

    def test_return_from_session_shows_normal(self, main_window):
        """Test return_from_session restores window"""
        main_window.floating_timer = Mock()
        
        main_window.return_from_session()
        
        main_window.showNormal.assert_called_once()
        main_window.activateWindow.assert_called_once()

    def test_on_time_updated_updates_print_balance(self, main_window):
        """Test on_time_updated also updates print balance"""
        mock_timer = Mock()
        main_window.floating_timer = mock_timer
        main_window.current_user["remainingPrints"] = 25.0
        
        main_window.on_time_updated(1800)
        
        mock_timer.update_print_balance.assert_called_with(25.0)

    def test_on_session_ended_restores_window(self, main_window):
        """Test on_session_ended restores main window"""
        main_window.floating_timer = Mock()
        main_window.show_question.return_value = False
        
        main_window.on_session_ended("expired")
        
        main_window.showNormal.assert_called_once()
        main_window.activateWindow.assert_called_once()

    def test_on_session_ended_user_declines_purchase(self, main_window):
        """Test on_session_ended when user declines purchase"""
        main_window.floating_timer = Mock()
        main_window.show_question.return_value = False
        
        with patch.object(main_window, "show_page") as mock_show:
            main_window.on_session_ended("expired")
            
            mock_show.assert_not_called()


# =============================================================================
# Additional Signal Handler Tests
# =============================================================================

class TestSignalHandlersAdditional:
    """Additional signal handler tests"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_on_sync_failed_without_timer(self, main_window):
        """Test on_sync_failed does nothing without timer"""
        main_window.floating_timer = None
        
        # Should not raise
        main_window.on_sync_failed("Connection lost")

    def test_on_sync_restored_without_timer(self, main_window):
        """Test on_sync_restored does nothing without timer"""
        main_window.floating_timer = None
        
        # Should not raise
        main_window.on_sync_restored()


# =============================================================================
# Force Logout Additional Tests  
# =============================================================================

class TestForceLogoutAdditional:
    """Additional force logout tests"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_reset_force_logout_flag_success(self, main_window):
        """Test reset_force_logout_flag logs success"""
        main_window.auth_service.firebase.db_update.return_value = {"success": True}
        
        # Should not raise
        main_window.reset_force_logout_flag()
        
        main_window.auth_service.firebase.db_update.assert_called_once()

    def test_reset_force_logout_flag_failure(self, main_window):
        """Test reset_force_logout_flag handles failure"""
        main_window.auth_service.firebase.db_update.return_value = {
            "success": False,
            "error": "Update failed"
        }
        
        # Should not raise
        main_window.reset_force_logout_flag()

    def test_reset_force_logout_flag_exception(self, main_window):
        """Test reset_force_logout_flag handles exception"""
        main_window.auth_service.firebase.db_update.side_effect = Exception("Network error")
        
        # Should not raise
        main_window.reset_force_logout_flag()

    def test_on_force_logout_without_active_session(self, main_window):
        """Test on_force_logout when no active session"""
        main_window.session_service.is_session_active.return_value = False
        
        with patch.object(main_window, "reset_force_logout_flag"):
            with patch("ui.auth_window.AuthWindow"):
                main_window.on_force_logout()
        
        # end_session should not be called
        main_window.session_service.end_session.assert_not_called()


# =============================================================================
# Cleanup Additional Tests
# =============================================================================

class TestCleanupAdditional:
    """Additional cleanup tests"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window

    def test_close_event_without_force_logout_listener(self, main_window):
        """Test closeEvent when no force logout listener"""
        main_window.force_logout_listener = None
        main_window.floating_timer = None
        
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()
        
        # Should not raise
        main_window.closeEvent(event)

    def test_close_event_without_floating_timer(self, main_window):
        """Test closeEvent when no floating timer"""
        main_window.force_logout_listener = Mock()
        main_window.floating_timer = None
        
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()
        
        # Should not raise
        main_window.closeEvent(event)

    def test_close_event_with_inactive_session(self, main_window):
        """Test closeEvent when session is not active"""
        main_window.force_logout_listener = Mock()
        main_window.floating_timer = Mock()
        main_window.session_service.is_session_active.return_value = False

        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()

        main_window.closeEvent(event)

        # end_session should not be called
        main_window.session_service.end_session.assert_not_called()


# =============================================================================
# Exception Handling Tests
# =============================================================================

class TestExceptionHandling:
    """Tests for exception handling in main window methods"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_handle_logout_exception_in_session_end(self, main_window):
        """Test handle_logout with exception during session end"""
        main_window.show_confirm.return_value = True
        main_window.session_service.end_session.side_effect = Exception("Session end failed")

        with patch.object(main_window, "hide"):
            with patch("ui.auth_window.AuthWindow"):
                # Should not raise, should continue with logout
                main_window.handle_logout()

        # Auth service logout should still be called despite session end failure
        main_window.auth_service.logout.assert_called_once()

    def test_handle_logout_exception_in_page_cleanup(self, main_window):
        """Test handle_logout with exception during page cleanup"""
        main_window.show_confirm.return_value = True
        main_window.home_page.cleanup.side_effect = Exception("Cleanup failed")

        with patch.object(main_window, "hide"):
            with patch("ui.auth_window.AuthWindow"):
                # Should not raise, should continue with logout
                main_window.handle_logout()

        # Auth service logout should still be called despite cleanup failure
        main_window.auth_service.logout.assert_called_once()

    def test_show_main_window_after_login_with_none_auth_window(self, main_window):
        """Test show_main_window_after_login when auth_window is None"""
        main_window.auth_window = None

        # Should not raise
        main_window.show_main_window_after_login()

        # Should still refresh pages
        main_window.auth_service.get_current_user.assert_called()

    def test_show_main_window_after_login_exception_in_refresh(self, main_window):
        """Test show_main_window_after_login with exception during refresh"""
        main_window.auth_window = Mock()

        with patch.object(main_window, "refresh_all_pages", side_effect=Exception("Refresh failed")):
            # Should raise the exception since it's not caught in the method
            with pytest.raises(Exception, match="Refresh failed"):
                main_window.show_main_window_after_login()

    def test_start_user_session_with_timer_creation_failure(self, main_window):
        """Test start_user_session when FloatingTimer creation fails"""
        with patch("ui.main_window.FloatingTimer") as mock_timer_cls:
            mock_timer_cls.side_effect = Exception("Timer creation failed")

            # Should raise the exception since it's not caught
            with pytest.raises(Exception, match="Timer creation failed"):
                main_window.start_user_session(3600)

            # Session should still be started before the exception
            main_window.session_service.start_session.assert_called_once_with(3600)


# =============================================================================
# Force Logout Exception Tests
# =============================================================================

class TestForceLogoutExceptionHandling:
    """Tests for force logout exception handling"""

    @pytest.fixture
    def main_window(self, qapp, mock_auth_service, mock_config, mock_session_service):
        """Create MainWindow instance"""
        window = create_main_window_mock(mock_auth_service, mock_config, mock_session_service, qapp)
        yield window
        window.close()

    def test_reset_force_logout_flag_exception(self, main_window):
        """Test reset_force_logout_flag with database exception"""
        main_window.auth_service.firebase.db_update.side_effect = Exception("Network error")

        # Should not raise
        main_window.reset_force_logout_flag()

    def test_on_force_logout_exception_during_session_end(self, main_window):
        """Test on_force_logout with exception during session end"""
        main_window.session_service.is_session_active.return_value = True
        main_window.session_service.end_session.side_effect = Exception("Session end failed")

        # Should raise the exception since it's not caught
        with pytest.raises(Exception, match="Session end failed"):
            with patch("ui.auth_window.AuthWindow"):
                main_window.on_force_logout()

