"""
Package Service
Fetch and manage packages from Firebase
Refactored to use base service for consistency
"""

from typing import Dict

from services.base_service import DatabaseService
from services.firebase_client import FirebaseClient
from utils.logger import get_logger


logger = get_logger(__name__)


class PackageService(DatabaseService):
    """Service for managing packages"""

    def __init__(self, firebase_client: FirebaseClient):
        super().__init__(firebase_client)

    def get_collection_name(self) -> str:
        """Return the collection name for packages"""
        return "packages"

    def get_all_packages(self) -> Dict:
        """
        Fetch all packages from Firebase using base service

        Returns:
            {
                'success': bool,
                'data': List[Dict] or [],
                'error': str (if failed)
            }
        """
        self.log_operation("get_all_packages")

        result = self.get_all_documents()

        if result.get("success"):
            packages = result.get("data", [])
            return self.create_success_response(
                packages, f"Fetched {len(packages)} packages"
            )
        else:
            return result

    def get_package_by_id(self, package_id: str) -> Dict:
        """Get single package by ID using base service"""
        self.log_operation("get_package_by_id", f"ID: {package_id}")

        result = self.get_document(package_id)

        if result.get("success"):
            package = result.get("data")
            if package:
                package["id"] = package_id
            return self.create_success_response(
                package, f"Package {package_id} retrieved"
            )
        else:
            return result

    @staticmethod
    def calculate_final_price(package: Dict) -> Dict:
        """
        Calculate final price after discount

        Returns:
            {
                'original_price': float,
                'discount_percent': float,
                'final_price': float,
                'savings': float
            }
        """
        original = package.get("price", 0)
        discount = package.get("discountPercent", 0)

        final = original * (1 - discount / 100)
        savings = original - final

        return {
            "original_price": original,
            "discount_percent": discount,
            "final_price": round(final, 2),
            "savings": round(savings, 2),
        }
