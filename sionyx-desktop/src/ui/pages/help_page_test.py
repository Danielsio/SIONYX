"""
Tests for help_page.py - Help Page UI Components
Tests FAQCard, ContactCard, and HelpPage initialization.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QWidget, QFrame, QScrollArea
from PyQt6.QtCore import Qt

from ui.pages.help_page import FAQCard, ContactCard, HelpPage


# =============================================================================
# FAQCard tests
# =============================================================================
class TestFAQCard:
    """Tests for FAQCard component"""

    def test_faq_card_initialization(self, qapp):
        """Test FAQCard stores question and answer"""
        card = FAQCard(icon="❓", question="How does it work?", answer="It works great!")
        assert card.question == "How does it work?"
        assert card.answer == "It works great!"

    def test_faq_card_stores_icon(self, qapp):
        """Test FAQCard stores icon"""
        card = FAQCard(icon="🔧", question="Q", answer="A")
        assert card.icon == "🔧"

    def test_faq_card_inherits_qframe(self, qapp):
        """Test FAQCard inherits from QFrame"""
        card = FAQCard(icon="📌", question="Q", answer="A")
        assert isinstance(card, QFrame)

    def test_faq_card_with_hebrew_content(self, qapp):
        """Test FAQCard with Hebrew text"""
        card = FAQCard(
            icon="⏱️",
            question="איך אני רוכש זמן?",
            answer="לחץ על 'חבילות' בתפריט הצד"
        )
        assert card.question == "איך אני רוכש זמן?"
        assert card.answer == "לחץ על 'חבילות' בתפריט הצד"

    def test_faq_card_with_parent(self, qapp):
        """Test FAQCard can have a parent widget"""
        parent = QWidget()
        card = FAQCard(icon="❓", question="Q", answer="A", parent=parent)
        assert card.parent() == parent

    def test_faq_card_has_shadow(self, qapp):
        """Test FAQCard has shadow effect applied"""
        card = FAQCard(icon="❓", question="Q", answer="A")
        assert card.graphicsEffect() is not None


# =============================================================================
# ContactCard tests
# =============================================================================
class TestContactCard:
    """Tests for ContactCard component"""

    def test_contact_card_initialization(self, qapp):
        """Test ContactCard stores title and value"""
        card = ContactCard(icon="📧", title="Email", value="test@example.com")
        assert card.title == "Email"
        assert card.value == "test@example.com"

    def test_contact_card_stores_icon(self, qapp):
        """Test ContactCard stores icon"""
        card = ContactCard(icon="📱", title="Phone", value="123-456")
        assert card.icon == "📱"

    def test_contact_card_inherits_qframe(self, qapp):
        """Test ContactCard inherits from QFrame"""
        card = ContactCard(icon="💬", title="Chat", value="Online")
        assert isinstance(card, QFrame)

    def test_contact_card_fixed_height(self, qapp):
        """Test ContactCard has fixed height"""
        card = ContactCard(icon="📧", title="Email", value="test@test.com")
        assert card.height() == 100

    def test_contact_card_with_hebrew(self, qapp):
        """Test ContactCard with Hebrew content"""
        card = ContactCard(icon="📧", title="אימייל", value="support@sionyx.co.il")
        assert card.title == "אימייל"

    def test_contact_card_with_parent(self, qapp):
        """Test ContactCard can have a parent widget"""
        parent = QWidget()
        card = ContactCard(icon="📱", title="T", value="V", parent=parent)
        assert card.parent() == parent

    def test_contact_card_has_shadow(self, qapp):
        """Test ContactCard has shadow effect applied"""
        card = ContactCard(icon="📧", title="Email", value="test@test.com")
        assert card.graphicsEffect() is not None


# =============================================================================
# HelpPage tests
# =============================================================================
class TestHelpPage:
    """Tests for HelpPage component"""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock auth service"""
        auth = Mock()
        auth.get_current_user.return_value = {
            "uid": "user123",
            "email": "test@example.com"
        }
        return auth

    def test_help_page_initialization(self, qapp, mock_auth_service):
        """Test HelpPage initializes correctly"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            assert page is not None

    def test_help_page_stores_auth_service(self, qapp, mock_auth_service):
        """Test HelpPage stores auth_service reference"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            assert page.auth_service == mock_auth_service

    def test_help_page_gets_current_user(self, qapp, mock_auth_service):
        """Test HelpPage fetches current user on init"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            mock_auth_service.get_current_user.assert_called_once()

    def test_help_page_stores_current_user(self, qapp, mock_auth_service):
        """Test HelpPage stores current user data"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            assert page.current_user["uid"] == "user123"

    def test_help_page_object_name(self, qapp, mock_auth_service):
        """Test HelpPage has correct object name"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            assert page.objectName() == "helpPage"

    def test_help_page_rtl_layout(self, qapp, mock_auth_service):
        """Test HelpPage uses RTL layout for Hebrew"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            assert page.layoutDirection() == Qt.LayoutDirection.RightToLeft

    def test_help_page_inherits_qwidget(self, qapp, mock_auth_service):
        """Test HelpPage inherits from QWidget"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            assert isinstance(page, QWidget)

    def test_help_page_with_parent(self, qapp, mock_auth_service):
        """Test HelpPage can have a parent widget"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            parent = QWidget()
            page = HelpPage(auth_service=mock_auth_service, parent=parent)
            assert page.parent() == parent

    def test_refresh_user_data_does_nothing(self, qapp, mock_auth_service):
        """Test refresh_user_data is a no-op for help page"""
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=mock_auth_service)
            # Should not raise
            page.refresh_user_data()

    def test_help_page_with_none_user(self, qapp):
        """Test HelpPage handles None user"""
        auth = Mock()
        auth.get_current_user.return_value = None
        
        with patch("ui.pages.help_page.get_logger") as mock_logger:
            mock_logger.return_value = Mock()
            page = HelpPage(auth_service=auth)
            assert page.current_user is None



