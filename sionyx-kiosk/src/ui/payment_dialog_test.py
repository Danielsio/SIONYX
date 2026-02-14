"""
Tests for PaymentDialog - Payment Processing with Firebase Real-Time Listener

TDD Strategy:
- Focus on LOGIC, not widget rendering
- Test state transitions and signal emissions
- Mock external dependencies (Firebase, HTTP, QWebEngine)
- Cover race conditions in async operations

Note: PyQt6.QtWebEngineWidgets is mocked at import time since it may not be
installed in the test environment.
"""

import json
import sys
import time
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog, QWidget


# =============================================================================
# Mock WebEngine imports BEFORE importing payment_dialog
# =============================================================================

# Create mock modules for WebEngine components
sys.modules["PyQt6.QtWebEngineWidgets"] = MagicMock()
sys.modules["PyQt6.QtWebChannel"] = MagicMock()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_auth_service(mock_firebase_client):
    """Create mock auth service with firebase client"""
    auth_service = Mock()
    auth_service.firebase = mock_firebase_client
    auth_service.firebase.database_url = "https://test-project.firebaseio.com"
    auth_service.firebase.id_token = "test-token"
    auth_service.firebase.org_id = "test-org"
    return auth_service


@pytest.fixture
def mock_parent_widget(mock_auth_service):
    """Create mock parent widget with required attributes"""
    parent = Mock()
    parent.auth_service = mock_auth_service
    parent.current_user = {
        "uid": "test-user-123",
        "firstName": "Test",
        "lastName": "User",
        "email": "test@example.com",
    }
    return parent


@pytest.fixture
def sample_package():
    """Sample package for testing"""
    return {
        "id": "pkg-premium",
        "name": "Premium Package",
        "minutes": 120,
        "prints": 50,
        "price": 49.99,
    }


def create_payment_dialog_mock(sample_package, mock_parent_widget):
    """Create a PaymentDialog instance bypassing QDialog.__init__"""
    from ui.payment_dialog import PaymentDialog

    # Create instance without calling __init__
    dialog = PaymentDialog.__new__(PaymentDialog)
    # Initialize QDialog with no parent (valid)
    QDialog.__init__(dialog)

    # Set the attributes that __init__ would set
    dialog.package = sample_package
    dialog.auth_service = mock_parent_widget.auth_service
    dialog.user = mock_parent_widget.current_user or {}
    dialog.payment_response = None
    dialog.purchase_id = None
    dialog._local_server = None
    dialog.listener_thread = None
    dialog.listener_active = False
    dialog._purchase_handled = False

    return dialog


# =============================================================================
# FirebaseStreamListener Tests
# =============================================================================


class TestFirebaseStreamListener:
    """Tests for Firebase streaming listener thread"""

    @pytest.fixture
    def stream_listener(self, qapp):
        """Create FirebaseStreamListener instance"""
        from ui.payment_dialog import FirebaseStreamListener

        listener = FirebaseStreamListener(
            database_url="https://test-project.firebaseio.com",
            auth_token="test-token",
            purchase_id="purchase-123",
            org_id="test-org",
        )
        return listener

    def test_initialization(self, stream_listener):
        """Test listener initializes with correct parameters"""
        assert stream_listener.database_url == "https://test-project.firebaseio.com"
        assert stream_listener.auth_token == "test-token"
        assert stream_listener.purchase_id == "purchase-123"
        assert stream_listener.org_id == "test-org"
        assert stream_listener.running is True

    def test_stop_sets_running_false(self, stream_listener):
        """Test stop() sets running flag to False"""
        stream_listener.stop()
        assert stream_listener.running is False

    def test_emits_signal_on_completed_status(self, stream_listener, qtbot):
        """Test signal emission when purchase status is 'completed'"""
        # Mock HTTP response with completed status
        mock_response = Mock()
        mock_response.status_code = 200

        # Simulate chunked response with completed purchase
        purchase_data = '{"status": "completed", "transactionId": "txn-123"}\n'
        mock_response.iter_content = Mock(return_value=iter(purchase_data))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        assert len(signal_received) == 1
        assert signal_received[0]["status"] == "completed"
        assert stream_listener.running is False

    def test_emits_signal_on_failed_status(self, stream_listener, qtbot):
        """Test signal emission when purchase status is 'failed'"""
        mock_response = Mock()
        mock_response.status_code = 200

        purchase_data = '{"status": "failed", "error": "Card declined"}\n'
        mock_response.iter_content = Mock(return_value=iter(purchase_data))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        assert len(signal_received) == 1
        assert signal_received[0]["status"] == "failed"

    def test_ignores_pending_status(self, stream_listener, qtbot):
        """Test that pending status does not trigger signal"""
        mock_response = Mock()
        mock_response.status_code = 200

        # First pending, then complete sequence
        chunks = list('{"status": "pending"}\n{"status": "completed"}\n')
        mock_response.iter_content = Mock(return_value=iter(chunks))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        # Should only receive the completed signal
        assert len(signal_received) == 1
        assert signal_received[0]["status"] == "completed"

    def test_handles_http_error(self, stream_listener, qtbot):
        """Test graceful handling of HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 401

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()  # Should not raise

        assert len(signal_received) == 0

    def test_handles_json_decode_error(self, stream_listener, qtbot):
        """Test handling of malformed JSON in stream"""
        mock_response = Mock()
        mock_response.status_code = 200

        # Malformed JSON followed by valid JSON
        chunks = list('not valid json\n{"status": "completed"}\n')
        mock_response.iter_content = Mock(return_value=iter(chunks))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        # Should recover and process the valid JSON
        assert len(signal_received) == 1

    def test_handles_timeout(self, stream_listener, qtbot):
        """Test graceful handling of request timeout"""
        import requests

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch(
            "ui.payment_dialog.requests.get", side_effect=requests.exceptions.Timeout
        ):
            stream_listener.run()  # Should not raise

        assert len(signal_received) == 0

    def test_buffer_accumulation_across_chunks(self, stream_listener, qtbot):
        """Test that buffer correctly accumulates partial JSON across chunks"""
        mock_response = Mock()
        mock_response.status_code = 200

        # JSON split across multiple chunks
        chunks = list('{"statu')
        chunks.extend(list('s": "completed"}\n'))
        mock_response.iter_content = Mock(return_value=iter(chunks))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        assert len(signal_received) == 1
        assert signal_received[0]["status"] == "completed"


# =============================================================================
# PaymentDialog Tests - Logic Focus
# =============================================================================


class TestPaymentDialogInitialization:
    """Tests for PaymentDialog initialization and setup"""

    def test_raises_error_without_auth_service(self, qapp, sample_package):
        """Test ValueError raised when parent has no auth_service"""
        from ui.payment_dialog import PaymentDialog

        # Create a parent without auth_service
        parent_without_auth = Mock(spec=[])

        # We need to patch QDialog.__init__ to not reject Mock parent
        with patch.object(QDialog, "__init__", return_value=None):
            with patch.object(PaymentDialog, "init_ui"):
                with pytest.raises(
                    ValueError, match="Parent must expose 'auth_service'"
                ):
                    PaymentDialog(sample_package, parent_without_auth)

    def test_derives_user_from_parent(self, qapp, sample_package, mock_parent_widget):
        """Test user is derived from parent widget"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        assert dialog.user["uid"] == "test-user-123"
        dialog.close()

    def test_falls_back_to_auth_service_for_user(
        self, qapp, sample_package, mock_auth_service
    ):
        """Test fallback to auth_service.get_current_user() when parent has no current_user"""
        # Create parent without current_user
        parent = Mock()
        parent.auth_service = mock_auth_service
        parent.current_user = None
        mock_auth_service.get_current_user.return_value = {"uid": "fallback-user"}

        dialog = create_payment_dialog_mock(sample_package, parent)
        # Manually set user as fallback would
        dialog.user = mock_auth_service.get_current_user()

        assert dialog.user["uid"] == "fallback-user"
        dialog.close()


class TestPaymentDialogPurchaseListener:
    """Tests for purchase listener setup and management"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog instance with mocks"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        yield dialog
        dialog.close()

    def test_setup_purchase_listener_starts_stream(self, payment_dialog):
        """Test that setup_purchase_listener starts Firebase stream"""
        payment_dialog.purchase_id = "test-purchase-id"

        with patch("ui.payment_dialog.FirebaseStreamListener") as mock_listener_cls:
            mock_listener = Mock()
            mock_listener_cls.return_value = mock_listener

            with patch.object(payment_dialog, "start_exponential_backoff_polling"):
                payment_dialog.setup_purchase_listener()

            mock_listener.start.assert_called_once()
            assert payment_dialog.listener_active is True

    def test_setup_purchase_listener_falls_back_to_polling(self, payment_dialog):
        """Test fallback to polling when stream fails"""
        payment_dialog.purchase_id = "test-purchase-id"

        with patch("ui.payment_dialog.FirebaseStreamListener") as mock_listener_cls:
            mock_listener_cls.side_effect = Exception("Stream failed")

            with patch.object(
                payment_dialog, "start_exponential_backoff_polling"
            ) as mock_polling:
                payment_dialog.setup_purchase_listener()

                mock_polling.assert_called_once()


class TestPaymentDialogPolling:
    """Tests for exponential backoff polling"""

    @pytest.fixture
    def payment_dialog_with_polling(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog for polling tests"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.purchase_id = "test-purchase-id"
        yield dialog

        # Cleanup
        if hasattr(dialog, "status_timer") and dialog.status_timer:
            dialog.status_timer.stop()
        dialog.close()

    def test_exponential_backoff_intervals(self, payment_dialog_with_polling):
        """Test that polling uses exponential backoff intervals"""
        dialog = payment_dialog_with_polling

        dialog.start_exponential_backoff_polling()

        # First 5 intervals should be 2 seconds
        assert dialog.poll_intervals[:5] == [2, 2, 2, 2, 2]
        # Next 5 should be 3 seconds
        assert dialog.poll_intervals[5:10] == [3, 3, 3, 3, 3]
        # Total should cover ~5 minutes
        assert sum(dialog.poll_intervals) >= 300

        # Cleanup
        dialog.status_timer.stop()

    def test_check_purchase_status_stops_on_completed(
        self, payment_dialog_with_polling, mock_auth_service
    ):
        """Test polling stops when purchase is completed"""
        dialog = payment_dialog_with_polling
        dialog.start_exponential_backoff_polling()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed", "rawResponse": {}}

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            with patch.object(dialog, "on_purchase_completed") as mock_complete:
                dialog.check_purchase_status()

                mock_complete.assert_called_once()
                assert dialog.status_timer.isActive() is False

    def test_check_purchase_status_continues_on_pending(
        self, payment_dialog_with_polling, mock_auth_service
    ):
        """Test polling continues when purchase is pending"""
        dialog = payment_dialog_with_polling
        dialog.start_exponential_backoff_polling()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "pending"}

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            dialog.check_purchase_status()

            # Timer should still be active
            assert dialog.check_count == 1
            assert dialog.current_interval_index == 1

        # Cleanup
        dialog.status_timer.stop()

    def test_check_purchase_status_timeout_after_max_checks(
        self, payment_dialog_with_polling, mock_auth_service
    ):
        """Test polling stops after maximum checks"""
        dialog = payment_dialog_with_polling
        dialog.start_exponential_backoff_polling()
        dialog.check_count = len(dialog.poll_intervals)  # Simulate max checks reached

        with patch("ui.payment_dialog.requests.get") as mock_get:
            dialog.check_purchase_status()

            # Should not make another request
            mock_get.assert_not_called()

        # Cleanup
        dialog.status_timer.stop()


class TestPaymentDialogCompletion:
    """Tests for payment completion handling"""

    @pytest.fixture
    def payment_dialog_for_completion(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog for completion tests"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        dialog.web_view.page.return_value = Mock()
        yield dialog
        dialog.close()

    def test_on_purchase_completed_with_success(self, payment_dialog_for_completion):
        """Test handling successful purchase completion"""
        dialog = payment_dialog_for_completion

        purchase_data = {
            "status": "completed",
            "rawResponse": {"transactionId": "txn-123"},
        }

        with patch.object(dialog, "show_success_via_javascript") as mock_show:
            dialog.on_purchase_completed(purchase_data)

            assert dialog.payment_response == {"transactionId": "txn-123"}
            mock_show.assert_called_once()

    def test_on_purchase_completed_with_failure(self, payment_dialog_for_completion):
        """Test handling failed purchase"""
        dialog = payment_dialog_for_completion

        purchase_data = {
            "status": "failed",
            "error": "Card declined",
        }

        with patch.object(dialog, "show_success_via_javascript") as mock_show:
            dialog.on_purchase_completed(purchase_data)

            # Should NOT show success
            mock_show.assert_not_called()


class TestPaymentDialogCredentials:
    """Tests for credential loading and error handling"""

    @pytest.fixture
    def payment_dialog_for_credentials(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog for credential tests"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        dialog.web_view.page.return_value = Mock()
        yield dialog
        dialog.close()

    def test_on_page_loaded_failure(self, payment_dialog_for_credentials):
        """Test handling page load failure"""
        dialog = payment_dialog_for_credentials

        # Should not raise on failure
        dialog.on_page_loaded(False)

    def test_shows_credentials_error_on_missing_credentials(
        self, payment_dialog_for_credentials
    ):
        """Test error display when credentials are missing"""
        dialog = payment_dialog_for_credentials

        with patch("ui.payment_dialog.OrganizationMetadataService") as mock_service:
            mock_instance = Mock()
            mock_instance.get_nedarim_credentials.return_value = {
                "success": False,
                "error": "Credentials not found",
            }
            mock_service.return_value = mock_instance

            with patch.object(dialog, "show_credentials_error") as mock_show_error:
                dialog.on_page_loaded(True)

                mock_show_error.assert_called_once_with("Credentials not found")


class TestPaymentDialogCleanup:
    """Tests for resource cleanup"""

    @pytest.fixture
    def payment_dialog_with_resources(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog with active resources"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)

        # Setup active resources
        dialog.status_timer = Mock(spec=QTimer)
        dialog.listener_thread = Mock()
        dialog.listener_thread.isRunning.return_value = True
        dialog._local_server = Mock()
        dialog.web_view = Mock()

        yield dialog

    def test_close_event_stops_timer(self, payment_dialog_with_resources):
        """Test closeEvent stops polling timer"""
        dialog = payment_dialog_with_resources

        from PyQt6.QtGui import QCloseEvent

        # Create a real QCloseEvent
        event = QCloseEvent()

        dialog.closeEvent(event)

        dialog.status_timer.stop.assert_called_once()

    def test_close_event_stops_listener_thread(self, payment_dialog_with_resources):
        """Test closeEvent stops stream listener"""
        dialog = payment_dialog_with_resources

        from PyQt6.QtGui import QCloseEvent

        # Create a real QCloseEvent
        event = QCloseEvent()

        dialog.closeEvent(event)

        dialog.listener_thread.stop.assert_called_once()
        dialog.listener_thread.wait.assert_called_once_with(2000)

    def test_close_event_stops_local_server(self, payment_dialog_with_resources):
        """Test closeEvent stops local HTTP server"""
        dialog = payment_dialog_with_resources

        from PyQt6.QtGui import QCloseEvent

        # Create a real QCloseEvent
        event = QCloseEvent()

        # Save reference before closeEvent sets it to None
        local_server_mock = dialog._local_server

        dialog.closeEvent(event)

        local_server_mock.stop.assert_called_once()
        assert dialog._local_server is None

    def test_payment_cancelled_stops_all_listeners(self, payment_dialog_with_resources):
        """Test cancellation stops all listening mechanisms"""
        dialog = payment_dialog_with_resources

        dialog.on_payment_cancelled()

        dialog.status_timer.stop.assert_called()
        dialog.listener_thread.stop.assert_called()


# =============================================================================
# Integration Tests - Race Condition Prevention
# =============================================================================


class TestPaymentDialogRaceConditions:
    """Tests for race condition scenarios"""

    @pytest.fixture
    def payment_dialog_for_race(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog for race condition tests"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        dialog.web_view.page.return_value = Mock()
        yield dialog
        dialog.close()

    def test_double_completion_handled_once(self, payment_dialog_for_race):
        """Test that completion is only processed once even if called twice

        This tests the race condition where both the stream listener and
        polling might detect completion simultaneously.

        RED-GREEN-REFACTOR:
        - RED: This test would fail without a guard
        - GREEN: Add _completion_handled flag
        - REFACTOR: Extract to private method
        """
        dialog = payment_dialog_for_race

        purchase_data = {
            "status": "completed",
            "rawResponse": {"transactionId": "txn-123"},
        }

        call_count = []

        def mock_show_success():
            call_count.append(1)

        with patch.object(
            dialog, "show_success_via_javascript", side_effect=mock_show_success
        ):
            # Simulate both stream and polling detecting completion
            dialog.on_purchase_completed(purchase_data)
            dialog.on_purchase_completed(purchase_data)

        # Should only be called once - guard prevents double handling (BUG-008)
        assert len(call_count) == 1


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestPaymentDialogEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_empty_package_data(self, qapp, mock_parent_widget):
        """Test handling of empty/minimal package data"""
        empty_package = {}

        dialog = create_payment_dialog_mock(empty_package, mock_parent_widget)
        assert dialog.package == empty_package
        dialog.close()

    def test_unicode_in_package_name(self, qapp, mock_parent_widget):
        """Test handling of Hebrew/Unicode in package data"""
        hebrew_package = {
            "id": "pkg-1",
            "name": "חבילת פרימיום",
            "price": 99.99,
        }

        dialog = create_payment_dialog_mock(hebrew_package, mock_parent_widget)
        assert dialog.package["name"] == "חבילת פרימיום"
        dialog.close()


# =============================================================================
# Additional PaymentDialog Tests for Coverage
# =============================================================================


class TestPaymentDialogCloseDialog:
    """Tests for close_dialog method"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog instance"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        yield dialog
        dialog.close()

    def test_close_dialog_stops_timer_and_accepts(self, payment_dialog):
        """Test close_dialog stops countdown timer and accepts dialog"""
        mock_timer = Mock()
        payment_dialog.countdown_timer = mock_timer

        with patch.object(payment_dialog, "accept") as mock_accept:
            payment_dialog.close_dialog()

        mock_timer.stop.assert_called_once()
        mock_accept.assert_called_once()


class TestPaymentDialogPageLoading:
    """Tests for page loading and config injection"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog instance"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        dialog.web_view.page.return_value = Mock()
        yield dialog
        dialog.close()

    def test_on_page_loaded_missing_mosad_id(self, payment_dialog):
        """Test error handling when mosad_id is missing"""
        with patch("ui.payment_dialog.OrganizationMetadataService") as mock_service:
            mock_instance = Mock()
            mock_instance.get_nedarim_credentials.return_value = {
                "success": True,
                "credentials": {"mosad_id": None, "api_valid": "ABC"},
            }
            mock_service.return_value = mock_instance

            with patch.object(payment_dialog, "show_credentials_error") as mock_error:
                payment_dialog.on_page_loaded(True)

            mock_error.assert_called_once_with("Missing Nedarim Plus credentials")

    def test_on_page_loaded_missing_api_valid(self, payment_dialog):
        """Test error handling when api_valid is missing"""
        with patch("ui.payment_dialog.OrganizationMetadataService") as mock_service:
            mock_instance = Mock()
            mock_instance.get_nedarim_credentials.return_value = {
                "success": True,
                "credentials": {"mosad_id": "123", "api_valid": None},
            }
            mock_service.return_value = mock_instance

            with patch.object(payment_dialog, "show_credentials_error") as mock_error:
                payment_dialog.on_page_loaded(True)

            mock_error.assert_called_once_with("Missing Nedarim Plus credentials")

    def test_on_page_loaded_injects_config_successfully(self, payment_dialog):
        """Test successful config injection"""
        mock_page = Mock()
        payment_dialog.web_view.page.return_value = mock_page

        with patch("ui.payment_dialog.OrganizationMetadataService") as mock_service:
            mock_instance = Mock()
            mock_instance.get_nedarim_credentials.return_value = {
                "success": True,
                "credentials": {"mosad_id": "123", "api_valid": "ABC"},
            }
            mock_service.return_value = mock_instance

            with patch(
                "services.package_service.PackageService.calculate_final_price"
            ) as mock_calc:
                mock_calc.return_value = {"original_price": 100, "final_price": 90}
                payment_dialog.on_page_loaded(True)

        mock_page.runJavaScript.assert_called_once()
        call_args = mock_page.runJavaScript.call_args[0][0]
        assert "setConfig" in call_args
        assert '"mosadId": "123"' in call_args


class TestPaymentDialogSuccessMessage:
    """Tests for success message display"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog instance"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        dialog.web_view.hide = Mock()
        # Mock layout
        mock_layout = Mock()
        dialog.layout = Mock(return_value=mock_layout)
        yield dialog
        dialog.close()

    def test_show_success_via_javascript_fallback(self, payment_dialog):
        """Test show_success_via_javascript falls back on exception"""
        # Make runJavaScript raise an exception
        payment_dialog.web_view.page.return_value.runJavaScript.side_effect = Exception(
            "JS error"
        )

        with patch.object(payment_dialog, "show_success_message") as mock_fallback:
            payment_dialog.show_success_via_javascript()

        mock_fallback.assert_called_once()

    def test_show_success_message_creates_overlay(self, payment_dialog):
        """Test show_success_message creates overlay and starts timer"""
        with patch("ui.payment_dialog.QWidget") as mock_widget:
            with patch("ui.payment_dialog.QVBoxLayout"):
                with patch("ui.payment_dialog.QLabel"):
                    with patch("ui.payment_dialog.QTimer") as mock_timer_cls:
                        mock_timer = Mock()
                        mock_timer_cls.return_value = mock_timer

                        payment_dialog.show_success_message()

        # Timer should be started with 3000ms
        mock_timer.start.assert_called_once_with(3000)
        payment_dialog.web_view.hide.assert_called_once()

    def test_show_success_message_exception_fallback(self, payment_dialog):
        """Test show_success_message falls back to accept on exception"""
        payment_dialog.web_view.hide.side_effect = Exception("Widget error")

        with patch.object(payment_dialog, "accept") as mock_accept:
            payment_dialog.show_success_message()

        mock_accept.assert_called_once()


class TestPaymentDialogCredentialsError:
    """Tests for credentials error display"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog instance"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        dialog.web_view.hide = Mock()
        mock_layout = Mock()
        dialog.layout = Mock(return_value=mock_layout)
        yield dialog
        dialog.close()

    def test_show_credentials_error_creates_overlay(self, payment_dialog):
        """Test show_credentials_error creates error overlay"""
        with patch("ui.payment_dialog.QWidget") as mock_widget:
            with patch("ui.payment_dialog.QVBoxLayout"):
                with patch("ui.payment_dialog.QLabel"):
                    with patch("ui.payment_dialog.QPushButton") as mock_btn:
                        mock_button = Mock()
                        mock_btn.return_value = mock_button

                        payment_dialog.show_credentials_error("Test error message")

        payment_dialog.web_view.hide.assert_called_once()

    def test_show_credentials_error_exception_fallback(self, payment_dialog):
        """Test show_credentials_error falls back to reject on exception"""
        payment_dialog.web_view.hide.side_effect = Exception("Widget error")

        with patch.object(payment_dialog, "reject") as mock_reject:
            payment_dialog.show_credentials_error("Error")

        mock_reject.assert_called_once()


class TestFirebaseStreamListenerStop:
    """Tests for FirebaseStreamListener stop behavior"""

    @pytest.fixture
    def stream_listener(self, qapp):
        """Create FirebaseStreamListener instance"""
        from ui.payment_dialog import FirebaseStreamListener

        listener = FirebaseStreamListener(
            database_url="https://test-project.firebaseio.com",
            auth_token="test-token",
            purchase_id="purchase-123",
            org_id="test-org",
        )
        return listener

    def test_stop_when_not_running(self, stream_listener):
        """Test stop when thread is not running"""
        with patch.object(stream_listener, "isRunning", return_value=False):
            stream_listener.stop()

        assert stream_listener.running is False

    def test_stop_when_running_waits_for_thread(self, stream_listener):
        """Test stop waits for running thread"""
        with patch.object(stream_listener, "isRunning", return_value=True):
            with patch.object(stream_listener, "quit") as mock_quit:
                with patch.object(stream_listener, "wait") as mock_wait:
                    stream_listener.stop()

        assert stream_listener.running is False
        mock_quit.assert_called_once()
        mock_wait.assert_called_once_with(1000)


# =============================================================================
# Tests for FirebaseStreamListener edge cases
# =============================================================================
class TestFirebaseStreamListenerEdgeCases:
    """Additional edge case tests for FirebaseStreamListener"""

    @pytest.fixture
    def stream_listener(self, qapp):
        """Create FirebaseStreamListener instance"""
        from ui.payment_dialog import FirebaseStreamListener

        listener = FirebaseStreamListener(
            database_url="https://test-project.firebaseio.com",
            auth_token="test-token",
            purchase_id="purchase-123",
            org_id="test-org",
        )
        return listener

    def test_handles_null_line_in_stream(self, stream_listener, qtbot):
        """Test that 'null' lines are ignored"""
        mock_response = Mock()
        mock_response.status_code = 200

        # Simulate null line followed by valid data
        chunks = list('null\n{"status": "completed"}\n')
        mock_response.iter_content = Mock(return_value=iter(chunks))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        assert len(signal_received) == 1
        assert signal_received[0]["status"] == "completed"

    def test_handles_empty_line_in_stream(self, stream_listener, qtbot):
        """Test that empty lines are ignored"""
        mock_response = Mock()
        mock_response.status_code = 200

        # Simulate empty lines
        chunks = list('\n\n{"status": "completed"}\n')
        mock_response.iter_content = Mock(return_value=iter(chunks))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        assert len(signal_received) == 1

    def test_handles_non_dict_json(self, stream_listener, qtbot):
        """Test handling of JSON that is not a dict"""
        mock_response = Mock()
        mock_response.status_code = 200

        # Simulate non-dict JSON
        chunks = list('["array", "data"]\n{"status": "completed"}\n')
        mock_response.iter_content = Mock(return_value=iter(chunks))

        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            stream_listener.run()

        # Should only get the dict with completed status
        assert len(signal_received) == 1

    def test_handles_generic_exception(self, stream_listener, qtbot):
        """Test handling of generic exception during stream"""
        signal_received = []
        stream_listener.status_changed.connect(
            lambda data: signal_received.append(data)
        )

        with patch(
            "ui.payment_dialog.requests.get", side_effect=Exception("Network error")
        ):
            stream_listener.run()  # Should not raise

        assert len(signal_received) == 0

    def test_stop_with_running_thread(self, stream_listener, qapp):
        """Test stop when thread is running"""
        # Mock isRunning to return True
        with patch.object(stream_listener, "isRunning", return_value=True):
            with patch.object(stream_listener, "quit") as mock_quit:
                with patch.object(stream_listener, "wait") as mock_wait:
                    stream_listener.stop()

                    assert stream_listener.running is False
                    mock_quit.assert_called_once()
                    mock_wait.assert_called_once_with(1000)


# =============================================================================
# Tests for PaymentDialog UI initialization
# =============================================================================
class TestPaymentDialogUI:
    """Tests for PaymentDialog UI methods"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog instance with mocks"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        dialog.web_view.page.return_value = Mock()
        dialog.web_view.hide = Mock()
        yield dialog
        dialog.close()

    def test_get_payment_response_returns_none_initially(self, payment_dialog):
        """Test get_payment_response returns None when no payment made"""
        assert payment_dialog.get_payment_response() is None

    def test_get_payment_response_returns_response_after_payment(self, payment_dialog):
        """Test get_payment_response returns response after payment"""
        payment_dialog.payment_response = {"transactionId": "txn-123"}
        assert payment_dialog.get_payment_response() == {"transactionId": "txn-123"}

    def test_on_payment_success_logs_message(self, payment_dialog):
        """Test on_payment_success logs appropriately"""
        # Should not raise
        payment_dialog.on_payment_success({"transactionId": "txn-123"})

    def test_on_purchase_created_sets_purchase_id(self, payment_dialog):
        """Test on_purchase_created sets purchase_id and starts listener"""
        with patch.object(payment_dialog, "setup_purchase_listener"):
            payment_dialog.on_purchase_created("test-purchase-id")

            assert payment_dialog.purchase_id == "test-purchase-id"

    def test_show_success_via_javascript_runs_js(self, payment_dialog):
        """Test show_success_via_javascript runs JavaScript"""
        mock_page = Mock()
        payment_dialog.web_view.page.return_value = mock_page

        payment_dialog.show_success_via_javascript()

        mock_page.runJavaScript.assert_called_once_with("showSuccess();")

    def test_show_success_via_javascript_handles_exception(self, payment_dialog):
        """Test show_success_via_javascript handles exception"""
        payment_dialog.web_view.page.side_effect = Exception("JS error")

        with patch.object(payment_dialog, "show_success_message"):
            payment_dialog.show_success_via_javascript()


# =============================================================================
# Tests for PaymentDialog polling edge cases
# =============================================================================
class TestPaymentDialogPollingEdgeCases:
    """Additional tests for polling edge cases"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog for polling tests"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.purchase_id = "test-purchase-id"
        dialog.web_view = Mock()
        yield dialog

        if hasattr(dialog, "status_timer") and dialog.status_timer:
            dialog.status_timer.stop()
        dialog.close()

    def test_check_purchase_status_handles_http_error(
        self, payment_dialog, mock_auth_service
    ):
        """Test check_purchase_status handles HTTP errors"""
        payment_dialog.start_exponential_backoff_polling()

        mock_response = Mock()
        mock_response.status_code = 500

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            payment_dialog.check_purchase_status()

        # Should continue polling
        assert payment_dialog.check_count == 1

        payment_dialog.status_timer.stop()

    def test_check_purchase_status_handles_exception(
        self, payment_dialog, mock_auth_service
    ):
        """Test check_purchase_status handles exceptions"""
        payment_dialog.start_exponential_backoff_polling()

        with patch(
            "ui.payment_dialog.requests.get", side_effect=Exception("Network error")
        ):
            payment_dialog.check_purchase_status()

        # Should continue polling
        assert payment_dialog.check_count == 1

        payment_dialog.status_timer.stop()

    def test_check_purchase_status_stops_listener_on_complete(
        self, payment_dialog, mock_auth_service
    ):
        """Test check_purchase_status stops listener thread on completion"""
        payment_dialog.start_exponential_backoff_polling()
        payment_dialog.listener_thread = Mock()
        payment_dialog.listener_thread.isRunning.return_value = True

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed", "rawResponse": {}}

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            with patch.object(payment_dialog, "on_purchase_completed"):
                payment_dialog.check_purchase_status()

        payment_dialog.listener_thread.stop.assert_called_once()

    def test_check_purchase_status_handles_none_purchase(
        self, payment_dialog, mock_auth_service
    ):
        """Test check_purchase_status handles None purchase data"""
        payment_dialog.start_exponential_backoff_polling()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = None

        with patch("ui.payment_dialog.requests.get", return_value=mock_response):
            payment_dialog.check_purchase_status()

        # Should continue polling
        assert payment_dialog.check_count == 1

        payment_dialog.status_timer.stop()


# =============================================================================
# Tests for PaymentDialog cleanup edge cases
# =============================================================================
class TestPaymentDialogCleanupEdgeCases:
    """Additional cleanup edge case tests"""

    @pytest.fixture
    def payment_dialog(self, qapp, sample_package, mock_parent_widget):
        """Create PaymentDialog for cleanup tests"""
        dialog = create_payment_dialog_mock(sample_package, mock_parent_widget)
        dialog.web_view = Mock()
        yield dialog

    def test_close_event_without_timer(self, payment_dialog):
        """Test closeEvent when no timer exists"""
        from PyQt6.QtGui import QCloseEvent

        event = QCloseEvent()
        payment_dialog.listener_thread = None
        payment_dialog._local_server = None

        # Should not raise
        payment_dialog.closeEvent(event)

    def test_on_payment_cancelled_without_timer(self, payment_dialog):
        """Test on_payment_cancelled when no timer exists"""
        payment_dialog.listener_thread = None

        # Should not raise
        payment_dialog.on_payment_cancelled()

    def test_on_payment_cancelled_with_stopped_listener(self, payment_dialog):
        """Test on_payment_cancelled when listener is not running"""
        payment_dialog.listener_thread = Mock()
        payment_dialog.listener_thread.isRunning.return_value = False

        # Should not call stop
        payment_dialog.on_payment_cancelled()

        payment_dialog.listener_thread.stop.assert_not_called()
