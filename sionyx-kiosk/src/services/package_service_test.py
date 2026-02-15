"""
Tests for PackageService
"""

from unittest.mock import patch

import pytest

from services.package_service import PackageService


class TestPackageService:
    """Test cases for PackageService"""

    @pytest.fixture
    def package_service(self, mock_firebase_client):
        """Create PackageService instance with mocked dependencies"""
        with patch(
            "services.package_service.DatabaseService.__init__", return_value=None
        ):
            service = PackageService(mock_firebase_client)
            service.firebase = mock_firebase_client
            return service

    def test_initialization(self, mock_firebase_client):
        """Test PackageService initialization"""
        with patch(
            "services.package_service.DatabaseService.__init__", return_value=None
        ):
            service = PackageService(mock_firebase_client)
            service.firebase = mock_firebase_client
            assert service.firebase == mock_firebase_client

    def test_get_collection_name(self, package_service):
        """Test getting collection name"""
        assert package_service.get_collection_name() == "packages"

    # Tests for get_all_packages
    def test_get_all_packages_success(self, package_service):
        """Test getting all packages successfully"""
        packages_data = [
            {"id": "pkg-1", "name": "Basic", "price": 10, "minutes": 60},
            {"id": "pkg-2", "name": "Premium", "price": 25, "minutes": 180},
        ]

        with patch.object(
            package_service,
            "get_all_documents",
            return_value={"success": True, "data": packages_data},
        ):
            with patch.object(package_service, "log_operation"):
                with patch.object(
                    package_service,
                    "create_success_response",
                    return_value={"success": True, "data": packages_data},
                ):
                    result = package_service.get_all_packages()

        assert result["success"] is True
        assert len(result["data"]) == 2

    def test_get_all_packages_empty(self, package_service):
        """Test getting packages when none exist"""
        with patch.object(
            package_service,
            "get_all_documents",
            return_value={"success": True, "data": []},
        ):
            with patch.object(package_service, "log_operation"):
                with patch.object(
                    package_service,
                    "create_success_response",
                    return_value={"success": True, "data": []},
                ):
                    result = package_service.get_all_packages()

        assert result["success"] is True
        assert len(result["data"]) == 0

    def test_get_all_packages_failure(self, package_service):
        """Test getting packages with failure"""
        with patch.object(
            package_service,
            "get_all_documents",
            return_value={"success": False, "error": "Database error"},
        ):
            with patch.object(package_service, "log_operation"):
                result = package_service.get_all_packages()

        assert result["success"] is False

    # Tests for get_package_by_id
    def test_get_package_by_id_success(self, package_service):
        """Test getting single package by ID"""
        package_data = {"name": "Premium", "price": 25, "minutes": 180}

        with patch.object(
            package_service,
            "get_document",
            return_value={"success": True, "data": package_data},
        ):
            with patch.object(package_service, "log_operation"):
                with patch.object(
                    package_service, "create_success_response"
                ) as mock_response:
                    mock_response.return_value = {
                        "success": True,
                        "data": {**package_data, "id": "pkg-123"},
                    }
                    result = package_service.get_package_by_id("pkg-123")

        assert result["success"] is True
        assert result["data"]["id"] == "pkg-123"

    def test_get_package_by_id_not_found(self, package_service):
        """Test getting non-existent package"""
        with patch.object(
            package_service,
            "get_document",
            return_value={"success": True, "data": None},
        ):
            with patch.object(package_service, "log_operation"):
                with patch.object(
                    package_service,
                    "create_success_response",
                    return_value={"success": True, "data": None},
                ):
                    result = package_service.get_package_by_id("non-existent")

        assert result["success"] is True
        assert result["data"] is None

    def test_get_package_by_id_failure(self, package_service):
        """Test getting package with failure"""
        with patch.object(
            package_service,
            "get_document",
            return_value={"success": False, "error": "Not found"},
        ):
            with patch.object(package_service, "log_operation"):
                result = package_service.get_package_by_id("pkg-123")

        assert result["success"] is False

    # Tests for calculate_final_price
    def test_calculate_final_price_no_discount(self):
        """Test calculating price without discount"""
        package = {"price": 100, "discountPercent": 0}

        result = PackageService.calculate_final_price(package)

        assert result["original_price"] == 100
        assert result["discount_percent"] == 0
        assert result["final_price"] == 100.0
        assert result["savings"] == 0.0

    def test_calculate_final_price_with_discount(self):
        """Test calculating price with discount"""
        package = {"price": 100, "discountPercent": 20}

        result = PackageService.calculate_final_price(package)

        assert result["original_price"] == 100
        assert result["discount_percent"] == 20
        assert result["final_price"] == 80.0
        assert result["savings"] == 20.0

    def test_calculate_final_price_50_percent_discount(self):
        """Test calculating price with 50% discount"""
        package = {"price": 50, "discountPercent": 50}

        result = PackageService.calculate_final_price(package)

        assert result["final_price"] == 25.0
        assert result["savings"] == 25.0

    def test_calculate_final_price_100_percent_discount(self):
        """Test calculating price with 100% discount (free)"""
        package = {"price": 100, "discountPercent": 100}

        result = PackageService.calculate_final_price(package)

        assert result["final_price"] == 0.0
        assert result["savings"] == 100.0

    def test_calculate_final_price_missing_discount(self):
        """Test calculating price when discount is not set"""
        package = {"price": 75}

        result = PackageService.calculate_final_price(package)

        assert result["original_price"] == 75
        assert result["discount_percent"] == 0
        assert result["final_price"] == 75.0
        assert result["savings"] == 0.0

    def test_calculate_final_price_missing_price(self):
        """Test calculating price when price is not set"""
        package = {"discountPercent": 20}

        result = PackageService.calculate_final_price(package)

        assert result["original_price"] == 0
        assert result["final_price"] == 0.0
        assert result["savings"] == 0.0

    def test_calculate_final_price_rounding(self):
        """Test that final price is properly rounded"""
        package = {"price": 99.99, "discountPercent": 15}

        result = PackageService.calculate_final_price(package)

        # 99.99 * 0.85 = 84.9915, should round to 84.99
        assert result["final_price"] == 84.99
        assert result["savings"] == 15.0  # 99.99 - 84.99 = 15.00

    def test_calculate_final_price_decimal_discount(self):
        """Test calculating with decimal discount percentage"""
        package = {"price": 100, "discountPercent": 33.33}

        result = PackageService.calculate_final_price(package)

        assert result["discount_percent"] == 33.33
        assert result["final_price"] == 66.67
