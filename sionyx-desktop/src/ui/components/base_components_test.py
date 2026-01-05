"""
Tests for base_components.py - FROST Design System UI Components
Tests component initialization, structure, and behavior without testing specific styles.
"""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.components.base_components import (
    ActionButton,
    BaseCard,
    Divider,
    EmptyState,
    FrostCard,
    HeaderSection,
    IconButton,
    LoadingSpinner,
    PageHeader,
    StatCard,
    StatusBadge,
    apply_shadow,
    get_shadow_effect,
)


# =============================================================================
# apply_shadow function tests
# =============================================================================
class TestApplyShadow:
    """Tests for apply_shadow helper function"""

    def test_apply_shadow_default_level(self, qapp):
        """Test shadow is applied with default 'md' level"""
        widget = QWidget()
        apply_shadow(widget)

        effect = widget.graphicsEffect()
        assert effect is not None
        assert isinstance(effect, QGraphicsDropShadowEffect)

    def test_apply_shadow_sm_level(self, qapp):
        """Test shadow with 'sm' level"""
        widget = QWidget()
        apply_shadow(widget, "sm")

        effect = widget.graphicsEffect()
        assert effect is not None
        assert effect.blurRadius() == 12

    def test_apply_shadow_md_level(self, qapp):
        """Test shadow with 'md' level"""
        widget = QWidget()
        apply_shadow(widget, "md")

        effect = widget.graphicsEffect()
        assert effect is not None
        assert effect.blurRadius() == 20

    def test_apply_shadow_lg_level(self, qapp):
        """Test shadow with 'lg' level"""
        widget = QWidget()
        apply_shadow(widget, "lg")

        effect = widget.graphicsEffect()
        assert effect is not None
        assert effect.blurRadius() == 28

    def test_apply_shadow_xl_level(self, qapp):
        """Test shadow with 'xl' level"""
        widget = QWidget()
        apply_shadow(widget, "xl")

        effect = widget.graphicsEffect()
        assert effect is not None
        assert effect.blurRadius() == 40

    def test_apply_shadow_primary_level(self, qapp):
        """Test shadow with 'primary' level for accent styling"""
        widget = QWidget()
        apply_shadow(widget, "primary")

        effect = widget.graphicsEffect()
        assert effect is not None
        assert effect.blurRadius() == 24

    def test_apply_shadow_unknown_level_falls_back_to_md(self, qapp):
        """Test unknown shadow level defaults to 'md'"""
        widget = QWidget()
        apply_shadow(widget, "unknown_level")

        effect = widget.graphicsEffect()
        assert effect is not None
        assert effect.blurRadius() == 20  # md level

    def test_apply_shadow_x_offset_is_zero(self, qapp):
        """Test shadow x offset is always 0"""
        widget = QWidget()
        apply_shadow(widget, "lg")

        effect = widget.graphicsEffect()
        assert effect.xOffset() == 0


# =============================================================================
# FrostCard tests
# =============================================================================
class TestFrostCard:
    """Tests for FrostCard component"""

    def test_frost_card_initialization(self, qapp):
        """Test FrostCard is created as QFrame"""
        card = FrostCard()
        assert isinstance(card, QFrame)

    def test_frost_card_has_shadow_effect(self, qapp):
        """Test FrostCard has shadow effect applied"""
        card = FrostCard()
        effect = card.graphicsEffect()
        assert effect is not None
        assert isinstance(effect, QGraphicsDropShadowEffect)

    def test_frost_card_with_parent(self, qapp):
        """Test FrostCard can be created with parent"""
        parent = QWidget()
        card = FrostCard(parent=parent)
        assert card.parent() == parent


# =============================================================================
# StatCard tests
# =============================================================================
class TestStatCard:
    """Tests for StatCard component"""

    def test_stat_card_initialization(self, qapp):
        """Test StatCard is created with required parameters"""
        card = StatCard(title="Test Title", value="100")
        assert card.title == "Test Title"
        assert card.value == "100"

    def test_stat_card_with_subtitle(self, qapp):
        """Test StatCard stores subtitle"""
        card = StatCard(title="Title", value="50", subtitle="Units")
        assert card.subtitle == "Units"

    def test_stat_card_with_icon(self, qapp):
        """Test StatCard stores icon"""
        card = StatCard(title="Title", value="25", icon="🕐")
        assert card.icon == "🕐"

    def test_stat_card_has_value_label(self, qapp):
        """Test StatCard has value_label attribute"""
        card = StatCard(title="Time", value="30:00")
        assert hasattr(card, "value_label")
        assert card.value_label.text() == "30:00"

    def test_stat_card_value_label_object_name(self, qapp):
        """Test value_label has correct object name"""
        card = StatCard(title="Title", value="Value")
        assert card.value_label.objectName() == "timeValue"

    def test_stat_card_has_fixed_size(self, qapp):
        """Test StatCard has a fixed size set"""
        card = StatCard(title="Title", value="Value")
        size = card.size()
        # Just verify a size is set (specific values come from constants)
        assert size.width() > 0
        assert size.height() > 0

    def test_stat_card_inherits_frost_card(self, qapp):
        """Test StatCard inherits from FrostCard"""
        card = StatCard(title="Title", value="Value")
        assert isinstance(card, FrostCard)


# =============================================================================
# ActionButton tests
# =============================================================================
class TestActionButton:
    """Tests for ActionButton component"""

    def test_action_button_initialization(self, qapp):
        """Test ActionButton is created with text"""
        button = ActionButton(text="Click Me")
        assert button.text() == "Click Me"

    def test_action_button_default_variant(self, qapp):
        """Test ActionButton defaults to 'primary' variant"""
        button = ActionButton(text="Test")
        assert button.variant == "primary"

    def test_action_button_default_size(self, qapp):
        """Test ActionButton defaults to 'md' size"""
        button = ActionButton(text="Test")
        assert (
            button.size_attr == "md"
            if hasattr(button, "size_attr")
            else button.size == "md"
        )

    def test_action_button_secondary_variant(self, qapp):
        """Test ActionButton with secondary variant"""
        button = ActionButton(text="Test", variant="secondary")
        assert button.variant == "secondary"

    def test_action_button_danger_variant(self, qapp):
        """Test ActionButton with danger variant"""
        button = ActionButton(text="Delete", variant="danger")
        assert button.variant == "danger"

    def test_action_button_ghost_variant(self, qapp):
        """Test ActionButton with ghost variant"""
        button = ActionButton(text="Cancel", variant="ghost")
        assert button.variant == "ghost"

    def test_action_button_has_pointing_cursor(self, qapp):
        """Test ActionButton has pointing hand cursor"""
        button = ActionButton(text="Test")
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_action_button_inherits_qpushbutton(self, qapp):
        """Test ActionButton inherits from QPushButton"""
        button = ActionButton(text="Test")
        assert isinstance(button, QPushButton)


# =============================================================================
# PageHeader tests
# =============================================================================
class TestPageHeader:
    """Tests for PageHeader component"""

    def test_page_header_initialization(self, qapp):
        """Test PageHeader is created with title"""
        header = PageHeader(title="Welcome")
        assert header.title_text == "Welcome"

    def test_page_header_with_subtitle(self, qapp):
        """Test PageHeader stores subtitle"""
        header = PageHeader(title="Dashboard", subtitle="Manage your account")
        assert header.subtitle_text == "Manage your account"

    def test_page_header_empty_subtitle(self, qapp):
        """Test PageHeader with no subtitle"""
        header = PageHeader(title="Title Only")
        assert header.subtitle_text == ""

    def test_page_header_inherits_qframe(self, qapp):
        """Test PageHeader inherits from QFrame"""
        header = PageHeader(title="Test")
        assert isinstance(header, QFrame)

    def test_page_header_has_shadow(self, qapp):
        """Test PageHeader has primary shadow applied"""
        header = PageHeader(title="Test")
        effect = header.graphicsEffect()
        assert effect is not None
        assert effect.blurRadius() == 24  # primary level


# =============================================================================
# LoadingSpinner tests
# =============================================================================
class TestLoadingSpinner:
    """Tests for LoadingSpinner component"""

    def test_loading_spinner_default_message(self, qapp):
        """Test LoadingSpinner default message in Hebrew"""
        spinner = LoadingSpinner()
        assert spinner.message == "טוען..."

    def test_loading_spinner_custom_message(self, qapp):
        """Test LoadingSpinner with custom message"""
        spinner = LoadingSpinner(message="Loading data...")
        assert spinner.message == "Loading data..."

    def test_loading_spinner_inherits_qwidget(self, qapp):
        """Test LoadingSpinner inherits from QWidget"""
        spinner = LoadingSpinner()
        assert isinstance(spinner, QWidget)


# =============================================================================
# EmptyState tests
# =============================================================================
class TestEmptyState:
    """Tests for EmptyState component"""

    def test_empty_state_default_values(self, qapp):
        """Test EmptyState default icon and title"""
        empty = EmptyState()
        assert empty.icon == "📭"
        assert empty.title_text == "אין נתונים"

    def test_empty_state_custom_icon(self, qapp):
        """Test EmptyState with custom icon"""
        empty = EmptyState(icon="🔍")
        assert empty.icon == "🔍"

    def test_empty_state_custom_title(self, qapp):
        """Test EmptyState with custom title"""
        empty = EmptyState(title="No results found")
        assert empty.title_text == "No results found"

    def test_empty_state_with_subtitle(self, qapp):
        """Test EmptyState stores subtitle"""
        empty = EmptyState(subtitle="Try adjusting your search")
        assert empty.subtitle_text == "Try adjusting your search"

    def test_empty_state_empty_subtitle(self, qapp):
        """Test EmptyState with no subtitle"""
        empty = EmptyState()
        assert empty.subtitle_text == ""

    def test_empty_state_inherits_qwidget(self, qapp):
        """Test EmptyState inherits from QWidget"""
        empty = EmptyState()
        assert isinstance(empty, QWidget)


# =============================================================================
# StatusBadge tests
# =============================================================================
class TestStatusBadge:
    """Tests for StatusBadge component"""

    def test_status_badge_initialization(self, qapp):
        """Test StatusBadge is created with text"""
        badge = StatusBadge(text="Active")
        assert badge.text() == "Active"

    def test_status_badge_default_variant(self, qapp):
        """Test StatusBadge defaults to 'info' variant"""
        badge = StatusBadge(text="Status")
        assert badge.variant == "info"

    def test_status_badge_completed_variant(self, qapp):
        """Test StatusBadge with completed variant"""
        badge = StatusBadge(text="Done", variant="completed")
        assert badge.variant == "completed"

    def test_status_badge_success_variant(self, qapp):
        """Test StatusBadge with success variant"""
        badge = StatusBadge(text="Success", variant="success")
        assert badge.variant == "success"

    def test_status_badge_pending_variant(self, qapp):
        """Test StatusBadge with pending variant"""
        badge = StatusBadge(text="Waiting", variant="pending")
        assert badge.variant == "pending"

    def test_status_badge_warning_variant(self, qapp):
        """Test StatusBadge with warning variant"""
        badge = StatusBadge(text="Warning", variant="warning")
        assert badge.variant == "warning"

    def test_status_badge_failed_variant(self, qapp):
        """Test StatusBadge with failed variant"""
        badge = StatusBadge(text="Failed", variant="failed")
        assert badge.variant == "failed"

    def test_status_badge_error_variant(self, qapp):
        """Test StatusBadge with error variant"""
        badge = StatusBadge(text="Error", variant="error")
        assert badge.variant == "error"

    def test_status_badge_active_variant(self, qapp):
        """Test StatusBadge with active variant"""
        badge = StatusBadge(text="Active", variant="active")
        assert badge.variant == "active"

    def test_status_badge_unknown_variant_uses_default_colors(self, qapp):
        """Test unknown variant falls back to default colors"""
        badge = StatusBadge(text="Unknown", variant="unknown_variant")
        assert badge.variant == "unknown_variant"
        # Badge should still be created without error

    def test_status_badge_center_aligned(self, qapp):
        """Test StatusBadge has center alignment"""
        badge = StatusBadge(text="Center")
        assert badge.alignment() == Qt.AlignmentFlag.AlignCenter

    def test_status_badge_inherits_qlabel(self, qapp):
        """Test StatusBadge inherits from QLabel"""
        badge = StatusBadge(text="Test")
        assert isinstance(badge, QLabel)


# =============================================================================
# Divider tests
# =============================================================================
class TestDivider:
    """Tests for Divider component"""

    def test_divider_initialization(self, qapp):
        """Test Divider is created"""
        divider = Divider()
        assert isinstance(divider, QFrame)

    def test_divider_fixed_height(self, qapp):
        """Test Divider has fixed height of 1"""
        divider = Divider()
        assert divider.height() == 1

    def test_divider_with_parent(self, qapp):
        """Test Divider can be created with parent"""
        parent = QWidget()
        divider = Divider(parent=parent)
        assert divider.parent() == parent


# =============================================================================
# IconButton tests
# =============================================================================
class TestIconButton:
    """Tests for IconButton component"""

    def test_icon_button_initialization(self, qapp):
        """Test IconButton is created with icon"""
        button = IconButton(icon="⚙")
        assert button.text() == "⚙"

    def test_icon_button_default_size(self, qapp):
        """Test IconButton default size is 40x40"""
        button = IconButton(icon="🔔")
        assert button.width() == 40
        assert button.height() == 40

    def test_icon_button_custom_size(self, qapp):
        """Test IconButton with custom size"""
        button = IconButton(icon="✖", size=32)
        assert button.width() == 32
        assert button.height() == 32

    def test_icon_button_large_size(self, qapp):
        """Test IconButton with large size"""
        button = IconButton(icon="➕", size=64)
        assert button.width() == 64
        assert button.height() == 64

    def test_icon_button_has_pointing_cursor(self, qapp):
        """Test IconButton has pointing hand cursor"""
        button = IconButton(icon="🗑")
        assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_icon_button_inherits_qpushbutton(self, qapp):
        """Test IconButton inherits from QPushButton"""
        button = IconButton(icon="📌")
        assert isinstance(button, QPushButton)


# =============================================================================
# Legacy compatibility tests
# =============================================================================
class TestLegacyCompatibility:
    """Tests for legacy compatibility aliases"""

    def test_base_card_alias(self, qapp):
        """Test BaseCard is alias for FrostCard"""
        assert BaseCard is FrostCard

    def test_header_section_alias(self, qapp):
        """Test HeaderSection is alias for PageHeader"""
        assert HeaderSection is PageHeader

    def test_get_shadow_effect_returns_dict(self, qapp):
        """Test get_shadow_effect returns correct dictionary"""
        result = get_shadow_effect()
        assert isinstance(result, dict)
        assert "blur_radius" in result
        assert "x_offset" in result
        assert "y_offset" in result
        assert "color" in result

    def test_get_shadow_effect_default_values(self, qapp):
        """Test get_shadow_effect default values"""
        result = get_shadow_effect()
        assert result["blur_radius"] == 16
        assert result["x_offset"] == 0
        assert result["y_offset"] == 4
        assert result["color"] == "rgba(15, 23, 42, 0.12)"

    def test_get_shadow_effect_custom_values(self, qapp):
        """Test get_shadow_effect with custom values"""
        result = get_shadow_effect(blur_radius=20, y_offset=8, color="rgba(0,0,0,0.5)")
        assert result["blur_radius"] == 20
        assert result["y_offset"] == 8
        assert result["color"] == "rgba(0,0,0,0.5)"
