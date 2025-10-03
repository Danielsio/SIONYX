"""
Package Service
Fetch and manage packages from Firebase
"""

from typing import List, Dict, Optional
from services.firebase_client import FirebaseClient
from utils.logger import get_logger

logger = get_logger(__name__)


class PackageService:
    """Service for managing packages"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client

    def get_all_packages(self) -> Dict:
        """
        Fetch all packages from Firebase

        Returns:
            {
                'success': bool,
                'packages': List[Dict] or [],
                'error': str (if failed)
            }
        """
        logger.info("Fetching packages from Firebase")

        result = self.firebase.db_get('packages')

        if not result.get('success'):
            logger.error(f"Failed to fetch packages: {result.get('error')}")
            return {
                'success': False,
                'packages': [],
                'error': result.get('error', 'Unknown error')
            }

        data = result.get('data')

        # Handle empty database
        if data is None:
            logger.warning("No packages found in database")
            return {
                'success': True,
                'packages': []
            }

        # Convert Firebase dict to list with IDs
        packages = []
        for pkg_id, pkg_data in data.items():
            pkg_data['id'] = pkg_id
            packages.append(pkg_data)

        logger.info(f"Fetched {len(packages)} packages")
        return {
            'success': True,
            'packages': packages
        }

    def get_package_by_id(self, package_id: str) -> Dict:
        """Get single package by ID"""
        logger.info(f"Fetching package: {package_id}")

        result = self.firebase.db_get(f'packages/{package_id}')

        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('error')
            }

        package = result.get('data')
        if package:
            package['id'] = package_id

        return {
            'success': True,
            'package': package
        }

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
        original = package.get('price', 0)
        discount = package.get('discountPercent', 0)

        final = original * (1 - discount / 100)
        savings = original - final

        return {
            'original_price': original,
            'discount_percent': discount,
            'final_price': round(final, 2),
            'savings': round(savings, 2)
        }