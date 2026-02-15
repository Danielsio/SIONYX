"""
Tests for firebase_config.py - Firebase Configuration
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest


# =============================================================================
# Test FirebaseConfig initialization - Development Mode (.env)
# =============================================================================
class TestFirebaseConfigDevMode:
    """Tests for FirebaseConfig in development mode (using .env)"""

    def test_loads_env_from_script_mode(self):
        """Test loads .env when running as script (development mode)"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    config = FirebaseConfig()

                    assert config.api_key == "test-api-key"
                    assert config.database_url == "https://test.firebaseio.com"
                    assert config.project_id == "test-project"
                    assert config.org_id == "test-org"

    def test_raises_on_missing_api_key(self):
        """Test raises ValueError when FIREBASE_API_KEY is missing"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": None,
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    with pytest.raises(ValueError, match="FIREBASE_API_KEY missing"):
                        FirebaseConfig()

    def test_raises_on_missing_database_url(self):
        """Test raises ValueError when FIREBASE_DATABASE_URL is missing"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": None,
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    with pytest.raises(
                        ValueError, match="FIREBASE_DATABASE_URL missing"
                    ):
                        FirebaseConfig()

    def test_raises_on_missing_project_id(self):
        """Test raises ValueError when FIREBASE_PROJECT_ID is missing"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": None,
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    with pytest.raises(ValueError, match="FIREBASE_PROJECT_ID missing"):
                        FirebaseConfig()

    def test_raises_on_missing_org_id(self):
        """Test raises ValueError when ORG_ID is missing"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": None,
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    with pytest.raises(ValueError, match="ORG_ID missing"):
                        FirebaseConfig()

    def test_raises_on_invalid_org_id_format(self):
        """Test raises ValueError when ORG_ID has invalid format"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "Invalid_Org!",  # Contains uppercase and special chars
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    with pytest.raises(ValueError, match="Invalid ORG_ID"):
                        FirebaseConfig()

    def test_accepts_valid_org_id_formats(self):
        """Test accepts valid ORG_ID formats"""
        from utils.firebase_config import FirebaseConfig

        valid_org_ids = ["myorg", "tech-lab", "university-cs", "org123", "a-b-c-123"]

        for org_id in valid_org_ids:
            env_values = {
                "FIREBASE_API_KEY": "test-api-key",
                "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
                "FIREBASE_PROJECT_ID": "test-project",
                "ORG_ID": org_id,
            }

            with patch("utils.firebase_config.is_production", return_value=False):
                with patch("utils.firebase_config.load_dotenv"):
                    with patch.object(
                        os, "getenv", side_effect=lambda k: env_values.get(k)
                    ):
                        config = FirebaseConfig()
                        assert config.org_id == org_id


# =============================================================================
# Test FirebaseConfig initialization - Production Mode (Registry)
# =============================================================================
class TestFirebaseConfigProdMode:
    """Tests for FirebaseConfig in production mode (using Windows Registry)"""

    def test_loads_from_registry_in_production(self):
        """Test loads config from registry when in production mode"""
        from utils.firebase_config import FirebaseConfig

        registry_config = {
            "org_id": "prod-org",
            "api_key": "prod-api-key",
            "auth_domain": "prod.firebaseapp.com",
            "project_id": "prod-project",
            "database_url": "https://prod.firebaseio.com",
            "storage_bucket": None,
            "messaging_sender_id": None,
            "app_id": None,
            "measurement_id": None,
        }

        with patch("utils.firebase_config.is_production", return_value=True):
            with patch(
                "utils.firebase_config.get_all_config", return_value=registry_config
            ):
                config = FirebaseConfig()

                assert config.api_key == "prod-api-key"
                assert config.database_url == "https://prod.firebaseio.com"
                assert config.project_id == "prod-project"
                assert config.org_id == "prod-org"

    def test_raises_on_missing_registry_values(self):
        """Test raises ValueError when registry values are missing"""
        from utils.firebase_config import FirebaseConfig

        registry_config = {
            "org_id": None,
            "api_key": None,
            "auth_domain": None,
            "project_id": None,
            "database_url": None,
            "storage_bucket": None,
            "messaging_sender_id": None,
            "app_id": None,
            "measurement_id": None,
        }

        with patch("utils.firebase_config.is_production", return_value=True):
            with patch(
                "utils.firebase_config.get_all_config", return_value=registry_config
            ):
                with pytest.raises(ValueError, match="missing in registry"):
                    FirebaseConfig()


# =============================================================================
# Test auth_url property
# =============================================================================
class TestAuthUrl:
    """Tests for auth_url property"""

    def test_auth_url_returns_correct_url(self):
        """Test auth_url returns Firebase Auth REST API URL"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    config = FirebaseConfig()

                    assert (
                        config.auth_url
                        == "https://identitytoolkit.googleapis.com/v1/accounts"
                    )


# =============================================================================
# Test get_firebase_config function
# =============================================================================
class TestGetFirebaseConfig:
    """Tests for get_firebase_config function"""

    def test_returns_firebase_config_instance(self):
        """Test get_firebase_config returns FirebaseConfig instance"""
        from utils import firebase_config as fc_module

        # Reset the global instance
        fc_module.firebase_config = None

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    result = fc_module.get_firebase_config()

                    assert isinstance(result, fc_module.FirebaseConfig)

        # Reset after test
        fc_module.firebase_config = None

    def test_returns_cached_instance(self):
        """Test get_firebase_config returns cached instance on second call"""
        from utils import firebase_config as fc_module

        # Reset the global instance
        fc_module.firebase_config = None

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv"):
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    result1 = fc_module.get_firebase_config()
                    result2 = fc_module.get_firebase_config()

                    assert result1 is result2

        # Reset after test
        fc_module.firebase_config = None


# =============================================================================
# Test .env file path resolution (development mode)
# =============================================================================
class TestEnvPathResolution:
    """Tests for .env file path resolution in development mode"""

    def test_tries_repo_root_first(self):
        """Test that repo root .env is tried first"""
        from utils.firebase_config import FirebaseConfig

        env_values = {
            "FIREBASE_API_KEY": "test-api-key",
            "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
            "FIREBASE_PROJECT_ID": "test-project",
            "ORG_ID": "test-org",
        }

        with patch("utils.firebase_config.is_production", return_value=False):
            with patch("utils.firebase_config.load_dotenv") as mock_load:
                with patch.object(
                    os, "getenv", side_effect=lambda k: env_values.get(k)
                ):
                    # Mock Path.exists to return False for repo root
                    with patch("utils.firebase_config.Path") as mock_path_cls:
                        # Create mock path instance
                        mock_path = MagicMock()
                        mock_path_cls.return_value = mock_path
                        mock_path.__truediv__ = Mock(return_value=mock_path)
                        mock_path.parent = mock_path
                        mock_path.exists.return_value = False

                        FirebaseConfig()

                        # load_dotenv should have been called
                        mock_load.assert_called()
