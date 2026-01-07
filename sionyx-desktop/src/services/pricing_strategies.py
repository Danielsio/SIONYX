"""
Pricing Strategies for Print Jobs

DESIGN PATTERN: Strategy
=========================
The Strategy pattern defines a family of algorithms, encapsulates each one,
and makes them interchangeable. This lets the algorithm vary independently
from clients that use it.

WHY STRATEGY HERE?
- Pricing logic might need different variations:
  - Standard pricing (B&W vs Color)
  - Student discounts (e.g., 20% off)
  - Bulk discounts (e.g., 10+ pages = 10% off)
  - Time-based pricing (cheaper at night)
  - Subscription/unlimited plans
- Without Strategy: lots of if/else in _calculate_cost()
- With Strategy: clean, testable, extensible

HOW IT WORKS:
1. PricingStrategy: Abstract base class defining the interface
2. Concrete strategies: StandardPricing, StudentPricing, BulkPricing, etc.
3. PrintMonitorService: Uses a strategy object, can swap at runtime

USAGE:
    # Set up with standard pricing
    service.pricing_strategy = StandardPricing(bw_price=1.0, color_price=3.0)

    # Later, switch to student pricing
    service.pricing_strategy = StudentPricing(bw_price=1.0, color_price=3.0, discount=0.2)

    # Cost calculation is delegated to the strategy
    cost = service.pricing_strategy.calculate_cost(pages=10, is_color=False)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from utils.logger import get_logger


logger = get_logger(__name__)


# =============================================================================
# Strategy Interface (Abstract Base Class)
# =============================================================================


class PricingStrategy(ABC):
    """
    Abstract base class for pricing strategies.

    All pricing strategies must implement calculate_cost().
    This is the "Strategy" in the Strategy pattern.
    """

    @abstractmethod
    def calculate_cost(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> float:
        """
        Calculate the cost for a print job.

        Args:
            pages: Number of pages in the document
            is_color: Whether the job is color (True) or B&W (False)
            copies: Number of copies being printed

        Returns:
            Total cost in NIS (or configured currency)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return human-readable name for this strategy."""
        pass

    def get_breakdown(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> dict:
        """
        Get detailed cost breakdown (for receipts/UI).

        Default implementation - subclasses can override for more detail.
        """
        total = self.calculate_cost(pages, is_color, copies)
        return {
            "pages": pages,
            "copies": copies,
            "is_color": is_color,
            "total": total,
            "strategy": self.get_name(),
        }


# =============================================================================
# Concrete Strategies
# =============================================================================


@dataclass
class StandardPricing(PricingStrategy):
    """
    Standard pricing strategy - simple per-page pricing.

    This is the default strategy: different prices for B&W and color.
    No discounts, no special logic.

    Example:
        strategy = StandardPricing(bw_price=1.0, color_price=3.0)
        cost = strategy.calculate_cost(pages=10, is_color=False)  # 10.0
        cost = strategy.calculate_cost(pages=10, is_color=True)   # 30.0
    """

    bw_price: float = 1.0  # Price per B&W page
    color_price: float = 3.0  # Price per color page

    def calculate_cost(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> float:
        """Calculate cost: pages × copies × price_per_page"""
        price_per_page = self.color_price if is_color else self.bw_price
        total_pages = pages * copies
        return total_pages * price_per_page

    def get_name(self) -> str:
        return "Standard"


@dataclass
class StudentPricing(PricingStrategy):
    """
    Student discount pricing strategy.

    Applies a percentage discount to the standard pricing.

    Example:
        strategy = StudentPricing(bw_price=1.0, color_price=3.0, discount_percent=20)
        cost = strategy.calculate_cost(pages=10, is_color=False)  # 8.0 (20% off)
    """

    bw_price: float = 1.0
    color_price: float = 3.0
    discount_percent: float = 20.0  # Percentage discount (e.g., 20 = 20%)

    def calculate_cost(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> float:
        """Calculate cost with student discount applied."""
        price_per_page = self.color_price if is_color else self.bw_price
        total_pages = pages * copies
        base_cost = total_pages * price_per_page

        # Apply discount
        discount_multiplier = 1 - (self.discount_percent / 100)
        return base_cost * discount_multiplier

    def get_name(self) -> str:
        return f"Student ({self.discount_percent}% off)"

    def get_breakdown(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> dict:
        """Include discount details in breakdown."""
        price_per_page = self.color_price if is_color else self.bw_price
        total_pages = pages * copies
        base_cost = total_pages * price_per_page
        discount_amount = base_cost * (self.discount_percent / 100)
        total = base_cost - discount_amount

        return {
            "pages": pages,
            "copies": copies,
            "is_color": is_color,
            "base_cost": base_cost,
            "discount_percent": self.discount_percent,
            "discount_amount": discount_amount,
            "total": total,
            "strategy": self.get_name(),
        }


@dataclass
class BulkPricing(PricingStrategy):
    """
    Bulk discount pricing strategy.

    Applies discount when printing above a threshold number of pages.

    Example:
        strategy = BulkPricing(
            bw_price=1.0,
            color_price=3.0,
            threshold=10,
            discount_percent=10
        )
        cost = strategy.calculate_cost(pages=5)   # 5.0 (no discount)
        cost = strategy.calculate_cost(pages=20)  # 18.0 (10% off)
    """

    bw_price: float = 1.0
    color_price: float = 3.0
    threshold: int = 10  # Pages needed for discount
    discount_percent: float = 10.0  # Discount when above threshold

    def calculate_cost(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> float:
        """Calculate cost with bulk discount if above threshold."""
        price_per_page = self.color_price if is_color else self.bw_price
        total_pages = pages * copies
        base_cost = total_pages * price_per_page

        # Apply discount only if above threshold
        if total_pages >= self.threshold:
            discount_multiplier = 1 - (self.discount_percent / 100)
            return base_cost * discount_multiplier

        return base_cost

    def get_name(self) -> str:
        return f"Bulk ({self.discount_percent}% off for {self.threshold}+ pages)"

    def get_breakdown(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> dict:
        """Include bulk discount details in breakdown."""
        price_per_page = self.color_price if is_color else self.bw_price
        total_pages = pages * copies
        base_cost = total_pages * price_per_page
        qualifies = total_pages >= self.threshold

        discount_amount = 0.0
        if qualifies:
            discount_amount = base_cost * (self.discount_percent / 100)

        total = base_cost - discount_amount

        return {
            "pages": pages,
            "copies": copies,
            "is_color": is_color,
            "base_cost": base_cost,
            "threshold": self.threshold,
            "qualifies_for_discount": qualifies,
            "discount_percent": self.discount_percent if qualifies else 0,
            "discount_amount": discount_amount,
            "total": total,
            "strategy": self.get_name(),
        }


@dataclass
class FlatRatePricing(PricingStrategy):
    """
    Flat rate pricing strategy - fixed cost regardless of pages.

    Useful for subscription plans or prepaid packages.

    Example:
        strategy = FlatRatePricing(flat_rate=0.0)  # Unlimited plan
        cost = strategy.calculate_cost(pages=100)  # 0.0

        strategy = FlatRatePricing(flat_rate=5.0)  # Fixed 5 NIS per job
        cost = strategy.calculate_cost(pages=100)  # 5.0
    """

    flat_rate: float = 0.0  # Fixed cost per print job

    def calculate_cost(
        self,
        pages: int,
        is_color: bool = False,
        copies: int = 1,
    ) -> float:
        """Return flat rate regardless of pages/color/copies."""
        return self.flat_rate

    def get_name(self) -> str:
        if self.flat_rate == 0:
            return "Unlimited"
        return f"Flat Rate ({self.flat_rate}₪)"


# =============================================================================
# Factory Function (Convenience)
# =============================================================================


def create_pricing_strategy(
    strategy_type: str,
    bw_price: float = 1.0,
    color_price: float = 3.0,
    **kwargs,
) -> PricingStrategy:
    """
    Factory function to create pricing strategies by name.

    Args:
        strategy_type: One of 'standard', 'student', 'bulk', 'flat'
        bw_price: Base B&W price per page
        color_price: Base color price per page
        **kwargs: Strategy-specific options

    Returns:
        PricingStrategy instance

    Example:
        strategy = create_pricing_strategy('student', discount_percent=25)
        strategy = create_pricing_strategy('bulk', threshold=20)
    """
    strategy_type = strategy_type.lower()

    if strategy_type == "standard":
        return StandardPricing(bw_price=bw_price, color_price=color_price)

    elif strategy_type == "student":
        discount = kwargs.get("discount_percent", 20.0)
        return StudentPricing(
            bw_price=bw_price,
            color_price=color_price,
            discount_percent=discount,
        )

    elif strategy_type == "bulk":
        threshold = kwargs.get("threshold", 10)
        discount = kwargs.get("discount_percent", 10.0)
        return BulkPricing(
            bw_price=bw_price,
            color_price=color_price,
            threshold=threshold,
            discount_percent=discount,
        )

    elif strategy_type in ("flat", "unlimited"):
        flat_rate = kwargs.get("flat_rate", 0.0)
        return FlatRatePricing(flat_rate=flat_rate)

    else:
        logger.warning(f"Unknown strategy '{strategy_type}', using standard")
        return StandardPricing(bw_price=bw_price, color_price=color_price)

