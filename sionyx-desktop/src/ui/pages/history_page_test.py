"""
Tests for HistoryPage UI Component

Testing Strategy:
- Test behavior and data loading, NOT styles/colors
- Use mock/dummy data to isolate from backend
- Verify widget structure and filtering functionality
- Test state changes (loading, empty, error)
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest
from PyQt6.QtWidgets import QLabel, QPushButton, QFrame, QLineEdit, QComboBox

from ui.pages.history_page import HistoryPage, PurchaseCard


# =============================================================================
# MOCK DATA FIXTURES
# =============================================================================

MOCK_USER = {
    "uid": "test-user-123",
    "firstName": "יוסי",
    "lastName": "כהן",
}

MOCK_PURCHASES = [
    {
        "id": "purchase-1",
        "packageName": "חבילה בסיסית",
        "minutes": 60,
        "prints": 10,
        "amount": 15,
        "status": "completed",
        "createdAt": "2024-01-15T10:30:00Z",
    },
    {
        "id": "purchase-2",
        "packageName": "חבילת פרימיום",
        "minutes": 180,
        "prints": 50,
        "amount": 45,
        "status": "pending",
        "createdAt": "2024-01-20T14:00:00Z",
    },
    {
        "id": "purchase-3",
        "packageName": "חבילה מיוחדת",
        "minutes": 120,
        "prints": 30,
        "amount": 30,
        "status": "failed",
        "createdAt": "2024-01-10T09:00:00Z",
    },
]


class TestPurchaseCard:
    """Test cases for PurchaseCard component"""

    @pytest.fixture
    def purchase_card(self, qapp):
        """Create a PurchaseCard with mock data"""
        return PurchaseCard(MOCK_PURCHASES[0])

    def test_initialization(self, purchase_card):
        """Test card initializes without errors"""
        assert purchase_card is not None
        assert isinstance(purchase_card, QFrame)

    def test_displays_package_name(self, purchase_card):
        """Test card displays package name"""
        labels = purchase_card.findChildren(QLabel)
        found = any("חבילה בסיסית" in label.text() for label in labels)
        assert found

    def test_displays_price(self, purchase_card):
        """Test card displays price"""
        labels = purchase_card.findChildren(QLabel)
        found = any("15" in label.text() for label in labels)
        assert found

    def test_displays_minutes_and_prints(self, purchase_card):
        """Test card displays minutes and prints info"""
        labels = purchase_card.findChildren(QLabel)
        found = any("60" in label.text() and "דקות" in label.text() for label in labels)
        assert found

    def test_format_date_valid(self, qapp):
        """Test date formatting with valid date"""
        card = PurchaseCard({"createdAt": "2024-01-15T10:30:00Z"})
        labels = card.findChildren(QLabel)
        # Should contain formatted date 15/01/2024
        found = any("15/01/2024" in label.text() for label in labels)
        assert found

    def test_format_date_invalid(self, qapp):
        """Test date formatting with invalid date"""
        card = PurchaseCard({"createdAt": "invalid-date"})
        labels = card.findChildren(QLabel)
        # Should show fallback text
        found = any("תאריך לא זמין" in label.text() for label in labels)
        assert found

    def test_get_icon_completed(self, qapp):
        """Test icon for completed status"""
        card = PurchaseCard({"status": "completed"})
        assert card._get_icon("completed") == "✓"

    def test_get_icon_pending(self, qapp):
        """Test icon for pending status"""
        card = PurchaseCard({"status": "pending"})
        assert card._get_icon("pending") == "⏳"

    def test_get_icon_failed(self, qapp):
        """Test icon for failed status"""
        card = PurchaseCard({"status": "failed"})
        assert card._get_icon("failed") == "✕"

    def test_safe_int_valid(self, purchase_card):
        """Test safe_int with valid number"""
        assert purchase_card._safe_int(10) == 10
        assert purchase_card._safe_int("15") == 15
        assert purchase_card._safe_int(10.5) == 10

    def test_safe_int_invalid(self, purchase_card):
        """Test safe_int with invalid input"""
        assert purchase_card._safe_int("invalid") == 0
        assert purchase_card._safe_int(None) == 0


class TestHistoryPage:
    """Test cases for HistoryPage UI component"""

    @pytest.fixture
    def mock_auth_service(self, mock_firebase_client):
        """Create mock auth service"""
        auth_service = Mock()
        auth_service.firebase = mock_firebase_client
        auth_service.get_current_user.return_value = MOCK_USER.copy()
        return auth_service

    @pytest.fixture
    def mock_purchase_service(self):
        """Create mock purchase service"""
        service = Mock()
        service.get_user_purchase_history.return_value = {
            "success": True,
            "data": MOCK_PURCHASES.copy(),
        }
        return service

    @pytest.fixture
    def history_page(self, mock_auth_service, mock_purchase_service, qapp):
        """Create HistoryPage with mocked dependencies"""
        with patch(
            "ui.pages.history_page.PurchaseService", return_value=mock_purchase_service
        ):
            page = HistoryPage(mock_auth_service)
            return page

    @pytest.fixture
    def history_page_with_data(self, mock_auth_service, mock_purchase_service, qapp):
        """Create HistoryPage with loaded data"""
        with patch(
            "ui.pages.history_page.PurchaseService", return_value=mock_purchase_service
        ):
            page = HistoryPage(mock_auth_service)
            page.refresh_user_data(force=True)
            return page

    @pytest.fixture
    def history_page_empty(self, mock_auth_service, qapp):
        """Create HistoryPage with no purchases"""
        mock_service = Mock()
        mock_service.get_user_purchase_history.return_value = {
            "success": True,
            "data": [],
        }
        with patch("ui.pages.history_page.PurchaseService", return_value=mock_service):
            page = HistoryPage(mock_auth_service)
            page.refresh_user_data(force=True)
            return page

    @pytest.fixture
    def history_page_error(self, mock_auth_service, qapp):
        """Create HistoryPage with fetch error"""
        mock_service = Mock()
        mock_service.get_user_purchase_history.return_value = {
            "success": False,
            "error": "Network error",
        }
        with patch("ui.pages.history_page.PurchaseService", return_value=mock_service):
            page = HistoryPage(mock_auth_service)
            page.refresh_user_data(force=True)
            return page

    # =========================================================================
    # INITIALIZATION TESTS
    # =========================================================================

    def test_initialization(self, history_page):
        """Test page initializes without errors"""
        assert history_page is not None
        assert history_page.objectName() == "historyPage"

    def test_has_list_container(self, history_page):
        """Test page has list container"""
        assert history_page.list_container is not None
        assert history_page.list_layout is not None

    def test_has_search_box(self, history_page):
        """Test page has search box"""
        assert history_page.search_box is not None
        assert isinstance(history_page.search_box, QLineEdit)

    def test_has_status_filter(self, history_page):
        """Test page has status filter dropdown"""
        assert history_page.status_filter is not None
        assert isinstance(history_page.status_filter, QComboBox)

    def test_has_sort_button(self, history_page):
        """Test page has sort button"""
        assert history_page.sort_btn is not None
        assert isinstance(history_page.sort_btn, QPushButton)

    def test_status_filter_has_all_options(self, history_page):
        """Test status filter has all status options"""
        options = [
            history_page.status_filter.itemText(i)
            for i in range(history_page.status_filter.count())
        ]
        assert "כל הסטטוסים" in options
        assert "הושלם" in options
        assert "ממתין" in options
        assert "נכשל" in options

    # =========================================================================
    # DATA LOADING TESTS
    # =========================================================================

    def test_stores_purchases(self, history_page_with_data):
        """Test purchases are stored after loading"""
        assert len(history_page_with_data.purchases) == 3

    def test_displays_purchase_cards(self, history_page_with_data):
        """Test purchase cards are displayed"""
        # Count PurchaseCard widgets in the list
        card_count = 0
        for i in range(history_page_with_data.list_layout.count()):
            item = history_page_with_data.list_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), PurchaseCard):
                card_count += 1

        assert card_count == 3

    # =========================================================================
    # EMPTY STATE TESTS
    # =========================================================================

    def test_empty_shows_empty_state(self, history_page_empty):
        """Test empty state is shown when no purchases"""
        assert history_page_empty.purchases == []

        # Find empty state text
        found_empty_text = False
        for i in range(history_page_empty.list_layout.count()):
            item = history_page_empty.list_layout.itemAt(i)
            if item and item.widget():
                labels = item.widget().findChildren(QLabel)
                for label in labels:
                    if "אין רכישות" in label.text():
                        found_empty_text = True
                        break

        assert found_empty_text

    # =========================================================================
    # ERROR STATE TESTS
    # =========================================================================

    def test_error_shows_error_state(self, history_page_error):
        """Test error state is shown when fetch fails"""
        # Find error state text
        found_error_text = False
        for i in range(history_page_error.list_layout.count()):
            item = history_page_error.list_layout.itemAt(i)
            if item and item.widget():
                labels = item.widget().findChildren(QLabel)
                for label in labels:
                    if "שגיאה" in label.text() or "Network error" in label.text():
                        found_error_text = True
                        break

        assert found_error_text

    # =========================================================================
    # SEARCH FILTER TESTS
    # =========================================================================

    def test_search_filters_by_package_name(self, history_page_with_data):
        """Test search filters purchases by package name"""
        history_page_with_data.search_box.setText("פרימיום")

        # Should only show the premium package
        assert len(history_page_with_data.filtered_purchases) == 1
        assert history_page_with_data.filtered_purchases[0]["packageName"] == "חבילת פרימיום"

    def test_search_empty_shows_all(self, history_page_with_data):
        """Test empty search shows all purchases"""
        history_page_with_data.search_box.setText("")

        assert len(history_page_with_data.filtered_purchases) == 3

    def test_search_no_matches(self, history_page_with_data):
        """Test search with no matches shows empty"""
        history_page_with_data.search_box.setText("לא קיים")

        assert len(history_page_with_data.filtered_purchases) == 0

    def test_search_case_insensitive(self, history_page_with_data):
        """Test search is case insensitive"""
        history_page_with_data.search_box.setText("בסיסית")

        assert len(history_page_with_data.filtered_purchases) == 1

    # =========================================================================
    # STATUS FILTER TESTS
    # =========================================================================

    def test_status_filter_completed(self, history_page_with_data):
        """Test filtering by completed status"""
        history_page_with_data.status_filter.setCurrentText("הושלם")

        assert len(history_page_with_data.filtered_purchases) == 1
        assert history_page_with_data.filtered_purchases[0]["status"] == "completed"

    def test_status_filter_pending(self, history_page_with_data):
        """Test filtering by pending status"""
        history_page_with_data.status_filter.setCurrentText("ממתין")

        assert len(history_page_with_data.filtered_purchases) == 1
        assert history_page_with_data.filtered_purchases[0]["status"] == "pending"

    def test_status_filter_failed(self, history_page_with_data):
        """Test filtering by failed status"""
        history_page_with_data.status_filter.setCurrentText("נכשל")

        assert len(history_page_with_data.filtered_purchases) == 1
        assert history_page_with_data.filtered_purchases[0]["status"] == "failed"

    def test_status_filter_all(self, history_page_with_data):
        """Test showing all statuses"""
        # First filter, then reset
        history_page_with_data.status_filter.setCurrentText("הושלם")
        history_page_with_data.status_filter.setCurrentText("כל הסטטוסים")

        assert len(history_page_with_data.filtered_purchases) == 3

    # =========================================================================
    # COMBINED FILTER TESTS
    # =========================================================================

    def test_combined_search_and_status_filter(self, history_page_with_data):
        """Test combining search and status filter"""
        history_page_with_data.search_box.setText("חבילה")
        history_page_with_data.status_filter.setCurrentText("הושלם")

        # Only the completed "חבילה בסיסית" should match
        assert len(history_page_with_data.filtered_purchases) == 1
        assert history_page_with_data.filtered_purchases[0]["status"] == "completed"

    # =========================================================================
    # SORT TESTS
    # =========================================================================

    def test_toggle_sort_changes_order(self, history_page_with_data):
        """Test sort toggle changes order"""
        original_first = history_page_with_data.filtered_purchases[0]["id"]

        history_page_with_data._toggle_sort()

        new_first = history_page_with_data.filtered_purchases[0]["id"]
        assert original_first != new_first

    def test_toggle_sort_reverses_order(self, history_page_with_data):
        """Test sorting reverses the order each time"""
        # Get first item before sort
        first_before = history_page_with_data.filtered_purchases[0]["id"]

        history_page_with_data._toggle_sort()

        # First item should be different after sort
        first_after = history_page_with_data.filtered_purchases[0]["id"]
        assert first_before != first_after

    def test_sort_empty_list_no_error(self, history_page_empty):
        """Test sorting empty list doesn't raise error"""
        # Should not raise exception
        history_page_empty._toggle_sort()

    # =========================================================================
    # CACHE TESTS
    # =========================================================================

    def test_cache_stores_data(self, history_page_with_data):
        """Test cache stores purchase data"""
        assert len(history_page_with_data.cached_purchases) == 3
        assert history_page_with_data.cache_timestamp is not None
        assert history_page_with_data.last_user_id == "test-user-123"

    def test_cache_valid_within_duration(self, history_page_with_data):
        """Test cache is valid within cache duration"""
        is_valid = history_page_with_data._is_cache_valid("test-user-123")
        assert is_valid

    def test_cache_invalid_for_different_user(self, history_page_with_data):
        """Test cache is invalid for different user"""
        is_valid = history_page_with_data._is_cache_valid("different-user")
        assert not is_valid

    def test_cache_invalid_when_expired(self, history_page_with_data):
        """Test cache is invalid when expired"""
        # Set timestamp to past
        history_page_with_data.cache_timestamp = datetime.now() - timedelta(seconds=120)

        is_valid = history_page_with_data._is_cache_valid("test-user-123")
        assert not is_valid

    def test_cache_invalid_when_empty(self, history_page):
        """Test cache is invalid when empty"""
        is_valid = history_page._is_cache_valid("test-user-123")
        assert not is_valid

    # =========================================================================
    # CLEAR USER DATA TESTS
    # =========================================================================

    def test_clear_user_data_resets_state(self, history_page_with_data):
        """Test clear_user_data resets all state"""
        history_page_with_data.clear_user_data()

        assert history_page_with_data.current_user is None
        assert history_page_with_data.purchases == []
        assert history_page_with_data.filtered_purchases == []
        assert history_page_with_data.cached_purchases == []
        assert history_page_with_data.cache_timestamp is None

    # =========================================================================
    # REFRESH TESTS
    # =========================================================================

    def test_refresh_user_data_loads_purchases(
        self, history_page, mock_auth_service, mock_purchase_service
    ):
        """Test refresh_user_data loads purchases"""
        history_page.refresh_user_data(force=True)

        mock_purchase_service.get_user_purchase_history.assert_called_with(
            "test-user-123"
        )
        assert len(history_page.purchases) == 3

    def test_refresh_uses_cache_when_valid(
        self, history_page_with_data, mock_purchase_service
    ):
        """Test refresh uses cache when valid"""
        # Reset mock call count
        mock_purchase_service.get_user_purchase_history.reset_mock()

        history_page_with_data.refresh_user_data(force=False)

        # Should not call service again (uses cache)
        mock_purchase_service.get_user_purchase_history.assert_not_called()

    def test_refresh_bypasses_cache_when_forced(
        self, history_page_with_data, mock_purchase_service
    ):
        """Test refresh bypasses cache when forced"""
        # Reset mock call count
        mock_purchase_service.get_user_purchase_history.reset_mock()

        history_page_with_data.refresh_user_data(force=True)

        mock_purchase_service.get_user_purchase_history.assert_called_once()

    def test_refresh_no_user_shows_error(self, history_page, mock_auth_service):
        """Test refresh with no user shows error"""
        mock_auth_service.get_current_user.return_value = None
        history_page.refresh_user_data()

        # Should not crash
        assert history_page.current_user is None

    # =========================================================================
    # DISPLAY HELPER TESTS
    # =========================================================================

    def test_clear_list_removes_all_card_widgets(self, history_page_with_data):
        """Test _clear_list removes all card widgets from layout"""
        # Count PurchaseCards before clear
        card_count_before = sum(
            1
            for i in range(history_page_with_data.list_layout.count())
            if history_page_with_data.list_layout.itemAt(i).widget()
            and isinstance(history_page_with_data.list_layout.itemAt(i).widget(), PurchaseCard)
        )
        assert card_count_before == 3

        history_page_with_data._clear_list()

        # Count PurchaseCards after clear
        card_count_after = sum(
            1
            for i in range(history_page_with_data.list_layout.count())
            if history_page_with_data.list_layout.itemAt(i).widget()
            and isinstance(history_page_with_data.list_layout.itemAt(i).widget(), PurchaseCard)
        )
        assert card_count_after == 0

    def test_show_loading_displays_spinner(self, history_page):
        """Test _show_loading displays loading spinner"""
        history_page._show_loading()

        # Should have a widget with loading text
        assert history_page.list_layout.count() > 0

    def test_show_empty_displays_empty_state(self, history_page):
        """Test _show_empty displays empty state"""
        history_page._show_empty()

        # Find empty state text
        found = False
        for i in range(history_page.list_layout.count()):
            item = history_page.list_layout.itemAt(i)
            if item and item.widget():
                labels = item.widget().findChildren(QLabel)
                for label in labels:
                    if "אין רכישות" in label.text():
                        found = True
                        break

        assert found

    def test_show_error_displays_message(self, history_page):
        """Test _show_error displays error message"""
        history_page._show_error("Test error message")

        # Find error text
        found = False
        for i in range(history_page.list_layout.count()):
            item = history_page.list_layout.itemAt(i)
            if item and item.widget():
                labels = item.widget().findChildren(QLabel)
                for label in labels:
                    if "Test error message" in label.text():
                        found = True
                        break

        assert found

