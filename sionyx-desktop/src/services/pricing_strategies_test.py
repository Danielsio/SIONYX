"""
Tests for Pricing Strategies (Strategy Pattern)

Tests the different pricing strategies for print jobs:
- StandardPricing: Simple per-page pricing
- StudentPricing: Percentage discount
- BulkPricing: Discount above threshold
- FlatRatePricing: Fixed cost per job
"""

import pytest

from services.pricing_strategies import (
    BulkPricing,
    FlatRatePricing,
    PricingStrategy,
    StandardPricing,
    StudentPricing,
    create_pricing_strategy,
)


# =============================================================================
# StandardPricing Tests
# =============================================================================


class TestStandardPricing:
    """Tests for StandardPricing strategy"""

    def test_bw_single_page(self):
        """Single B&W page costs bw_price"""
        strategy = StandardPricing(bw_price=1.0, color_price=3.0)

        cost = strategy.calculate_cost(pages=1, is_color=False)

        assert cost == 1.0

    def test_bw_multiple_pages(self):
        """Multiple B&W pages: pages × bw_price"""
        strategy = StandardPricing(bw_price=1.0, color_price=3.0)

        cost = strategy.calculate_cost(pages=10, is_color=False)

        assert cost == 10.0

    def test_color_single_page(self):
        """Single color page costs color_price"""
        strategy = StandardPricing(bw_price=1.0, color_price=3.0)

        cost = strategy.calculate_cost(pages=1, is_color=True)

        assert cost == 3.0

    def test_color_multiple_pages(self):
        """Multiple color pages: pages × color_price"""
        strategy = StandardPricing(bw_price=1.0, color_price=3.0)

        cost = strategy.calculate_cost(pages=10, is_color=True)

        assert cost == 30.0

    def test_with_copies(self):
        """Copies multiply the cost"""
        strategy = StandardPricing(bw_price=1.0, color_price=3.0)

        cost = strategy.calculate_cost(pages=5, is_color=False, copies=3)

        assert cost == 15.0  # 5 pages × 3 copies × 1.0

    def test_custom_prices(self):
        """Custom prices are respected"""
        strategy = StandardPricing(bw_price=0.50, color_price=2.0)

        bw_cost = strategy.calculate_cost(pages=10, is_color=False)
        color_cost = strategy.calculate_cost(pages=10, is_color=True)

        assert bw_cost == 5.0
        assert color_cost == 20.0

    def test_get_name(self):
        """Returns 'Standard' as name"""
        strategy = StandardPricing()

        assert strategy.get_name() == "Standard"

    def test_get_breakdown(self):
        """Breakdown includes all details"""
        strategy = StandardPricing(bw_price=1.0, color_price=3.0)

        breakdown = strategy.get_breakdown(pages=5, is_color=True, copies=2)

        assert breakdown["pages"] == 5
        assert breakdown["copies"] == 2
        assert breakdown["is_color"] is True
        assert breakdown["total"] == 30.0  # 5 × 2 × 3.0
        assert breakdown["strategy"] == "Standard"


# =============================================================================
# StudentPricing Tests
# =============================================================================


class TestStudentPricing:
    """Tests for StudentPricing strategy"""

    def test_applies_discount(self):
        """Student discount is applied"""
        strategy = StudentPricing(
            bw_price=1.0, color_price=3.0, discount_percent=20.0
        )

        cost = strategy.calculate_cost(pages=10, is_color=False)

        assert cost == 8.0  # 10.0 - 20% = 8.0

    def test_zero_discount(self):
        """Zero discount = standard pricing"""
        strategy = StudentPricing(
            bw_price=1.0, color_price=3.0, discount_percent=0.0
        )

        cost = strategy.calculate_cost(pages=10, is_color=False)

        assert cost == 10.0

    def test_100_percent_discount(self):
        """100% discount = free"""
        strategy = StudentPricing(
            bw_price=1.0, color_price=3.0, discount_percent=100.0
        )

        cost = strategy.calculate_cost(pages=10, is_color=False)

        assert cost == 0.0

    def test_color_with_discount(self):
        """Discount applies to color too"""
        strategy = StudentPricing(
            bw_price=1.0, color_price=3.0, discount_percent=10.0
        )

        cost = strategy.calculate_cost(pages=10, is_color=True)

        assert cost == 27.0  # 30.0 - 10% = 27.0

    def test_get_name_includes_discount(self):
        """Name includes discount percentage"""
        strategy = StudentPricing(discount_percent=25.0)

        name = strategy.get_name()

        assert "25" in name
        assert "off" in name.lower()

    def test_get_breakdown_includes_discount_details(self):
        """Breakdown shows discount amount"""
        strategy = StudentPricing(
            bw_price=1.0, color_price=3.0, discount_percent=20.0
        )

        breakdown = strategy.get_breakdown(pages=10, is_color=False)

        assert breakdown["base_cost"] == 10.0
        assert breakdown["discount_percent"] == 20.0
        assert breakdown["discount_amount"] == 2.0
        assert breakdown["total"] == 8.0


# =============================================================================
# BulkPricing Tests
# =============================================================================


class TestBulkPricing:
    """Tests for BulkPricing strategy"""

    def test_no_discount_below_threshold(self):
        """No discount when below threshold"""
        strategy = BulkPricing(
            bw_price=1.0, color_price=3.0, threshold=10, discount_percent=10.0
        )

        cost = strategy.calculate_cost(pages=5, is_color=False)

        assert cost == 5.0  # No discount

    def test_discount_at_threshold(self):
        """Discount applied at exact threshold"""
        strategy = BulkPricing(
            bw_price=1.0, color_price=3.0, threshold=10, discount_percent=10.0
        )

        cost = strategy.calculate_cost(pages=10, is_color=False)

        assert cost == 9.0  # 10.0 - 10% = 9.0

    def test_discount_above_threshold(self):
        """Discount applied above threshold"""
        strategy = BulkPricing(
            bw_price=1.0, color_price=3.0, threshold=10, discount_percent=10.0
        )

        cost = strategy.calculate_cost(pages=20, is_color=False)

        assert cost == 18.0  # 20.0 - 10% = 18.0

    def test_copies_count_toward_threshold(self):
        """Total pages (pages × copies) counts toward threshold"""
        strategy = BulkPricing(
            bw_price=1.0, color_price=3.0, threshold=10, discount_percent=10.0
        )

        # 5 pages × 2 copies = 10 total pages (meets threshold)
        cost = strategy.calculate_cost(pages=5, is_color=False, copies=2)

        assert cost == 9.0  # 10.0 - 10% = 9.0

    def test_get_name_includes_threshold(self):
        """Name includes threshold"""
        strategy = BulkPricing(threshold=20, discount_percent=15.0)

        name = strategy.get_name()

        assert "20" in name
        assert "15" in name

    def test_get_breakdown_shows_qualification(self):
        """Breakdown shows whether qualifies for discount"""
        strategy = BulkPricing(threshold=10, discount_percent=10.0)

        below = strategy.get_breakdown(pages=5)
        above = strategy.get_breakdown(pages=15)

        assert below["qualifies_for_discount"] is False
        assert above["qualifies_for_discount"] is True


# =============================================================================
# FlatRatePricing Tests
# =============================================================================


class TestFlatRatePricing:
    """Tests for FlatRatePricing strategy"""

    def test_returns_flat_rate(self):
        """Always returns the flat rate"""
        strategy = FlatRatePricing(flat_rate=5.0)

        cost1 = strategy.calculate_cost(pages=1)
        cost100 = strategy.calculate_cost(pages=100)
        cost_color = strategy.calculate_cost(pages=50, is_color=True)

        assert cost1 == 5.0
        assert cost100 == 5.0
        assert cost_color == 5.0

    def test_zero_flat_rate_unlimited(self):
        """Zero flat rate = unlimited printing"""
        strategy = FlatRatePricing(flat_rate=0.0)

        cost = strategy.calculate_cost(pages=1000, is_color=True, copies=10)

        assert cost == 0.0

    def test_get_name_zero_shows_unlimited(self):
        """Zero rate shows 'Unlimited'"""
        strategy = FlatRatePricing(flat_rate=0.0)

        assert strategy.get_name() == "Unlimited"

    def test_get_name_nonzero_shows_rate(self):
        """Non-zero rate shows the amount"""
        strategy = FlatRatePricing(flat_rate=5.0)

        name = strategy.get_name()

        assert "5" in name
        assert "Flat" in name


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestCreatePricingStrategy:
    """Tests for create_pricing_strategy factory function"""

    def test_create_standard(self):
        """Creates StandardPricing"""
        strategy = create_pricing_strategy("standard")

        assert isinstance(strategy, StandardPricing)

    def test_create_student(self):
        """Creates StudentPricing with default discount"""
        strategy = create_pricing_strategy("student")

        assert isinstance(strategy, StudentPricing)

    def test_create_student_with_discount(self):
        """Creates StudentPricing with custom discount"""
        strategy = create_pricing_strategy("student", discount_percent=30)

        assert isinstance(strategy, StudentPricing)
        assert strategy.discount_percent == 30

    def test_create_bulk(self):
        """Creates BulkPricing"""
        strategy = create_pricing_strategy("bulk", threshold=20)

        assert isinstance(strategy, BulkPricing)
        assert strategy.threshold == 20

    def test_create_flat(self):
        """Creates FlatRatePricing"""
        strategy = create_pricing_strategy("flat", flat_rate=10.0)

        assert isinstance(strategy, FlatRatePricing)
        assert strategy.flat_rate == 10.0

    def test_create_unlimited(self):
        """'unlimited' creates FlatRatePricing with 0"""
        strategy = create_pricing_strategy("unlimited")

        assert isinstance(strategy, FlatRatePricing)
        assert strategy.flat_rate == 0.0

    def test_unknown_returns_standard(self):
        """Unknown type returns StandardPricing with warning"""
        strategy = create_pricing_strategy("unknown_strategy")

        assert isinstance(strategy, StandardPricing)

    def test_case_insensitive(self):
        """Strategy type is case insensitive"""
        strategy1 = create_pricing_strategy("STANDARD")
        strategy2 = create_pricing_strategy("Student")
        strategy3 = create_pricing_strategy("BULK")

        assert isinstance(strategy1, StandardPricing)
        assert isinstance(strategy2, StudentPricing)
        assert isinstance(strategy3, BulkPricing)

    def test_passes_prices(self):
        """Passes bw_price and color_price to strategy"""
        strategy = create_pricing_strategy(
            "standard", bw_price=0.5, color_price=2.0
        )

        assert strategy.bw_price == 0.5
        assert strategy.color_price == 2.0


# =============================================================================
# Integration Tests
# =============================================================================


class TestPricingStrategyIntegration:
    """Integration tests for pricing strategies"""

    def test_all_strategies_implement_interface(self):
        """All strategies implement PricingStrategy interface"""
        strategies = [
            StandardPricing(),
            StudentPricing(),
            BulkPricing(),
            FlatRatePricing(),
        ]

        for strategy in strategies:
            # All should be PricingStrategy instances
            assert isinstance(strategy, PricingStrategy)

            # All should have required methods
            assert hasattr(strategy, "calculate_cost")
            assert hasattr(strategy, "get_name")
            assert hasattr(strategy, "get_breakdown")

            # All methods should work
            cost = strategy.calculate_cost(pages=10)
            assert isinstance(cost, (int, float))

            name = strategy.get_name()
            assert isinstance(name, str)

            breakdown = strategy.get_breakdown(pages=10)
            assert isinstance(breakdown, dict)
            assert "total" in breakdown

    def test_strategy_comparison(self):
        """Compare costs across strategies for same job"""
        standard = StandardPricing(bw_price=1.0, color_price=3.0)
        student = StudentPricing(bw_price=1.0, color_price=3.0, discount_percent=20)
        bulk = BulkPricing(bw_price=1.0, color_price=3.0, threshold=5, discount_percent=10)
        unlimited = FlatRatePricing(flat_rate=0.0)

        # 10 page B&W job
        pages = 10

        standard_cost = standard.calculate_cost(pages)
        student_cost = student.calculate_cost(pages)
        bulk_cost = bulk.calculate_cost(pages)
        unlimited_cost = unlimited.calculate_cost(pages)

        # Verify expected order: standard > bulk > student > unlimited
        assert standard_cost == 10.0
        assert student_cost == 8.0  # 20% off
        assert bulk_cost == 9.0  # 10% off (above threshold)
        assert unlimited_cost == 0.0

