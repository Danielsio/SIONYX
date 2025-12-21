"""
Tests for firebase_config.py - Firebase configuration
Tests configuration loading and validation.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from utils.firebase_config import FirebaseConfig


# =============================================================================
# FirebaseConfig initialization tests
# =============================================================================
class TestFirebaseConfigInit:
    """Tests for FirebaseConfig initialization"""

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_loads_api_key(self, mock_dotenv):
        """Test API key is loaded from env"""
        config = FirebaseConfig()
        assert config.api_key == "test_api_key"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_loads_database_url(self, mock_dotenv):
        """Test database URL is loaded from env"""
        config = FirebaseConfig()
        assert config.database_url == "https://test.firebaseio.com"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_loads_project_id(self, mock_dotenv):
        """Test project ID is loaded from env"""
        config = FirebaseConfig()
        assert config.project_id == "test-project"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_loads_org_id(self, mock_dotenv):
        """Test org ID is loaded from env"""
        config = FirebaseConfig()
        assert config.org_id == "test-org"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "my-org-123"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_loads_auth_domain(self, mock_dotenv):
        """Test auth domain is loaded from env"""
        config = FirebaseConfig()
        assert config.auth_domain == "test.firebaseapp.com"


# =============================================================================
# Validation tests
# =============================================================================
class TestFirebaseConfigValidation:
    """Tests for FirebaseConfig validation"""

    @patch.dict(os.environ, {
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    }, clear=True)
    @patch("utils.firebase_config.load_dotenv")
    def test_missing_api_key_raises(self, mock_dotenv):
        """Test missing API key raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FirebaseConfig()
        assert "FIREBASE_API_KEY" in str(exc_info.value)

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    }, clear=True)
    @patch("utils.firebase_config.load_dotenv")
    def test_missing_database_url_raises(self, mock_dotenv):
        """Test missing database URL raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FirebaseConfig()
        assert "FIREBASE_DATABASE_URL" in str(exc_info.value)

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "ORG_ID": "test-org"
    }, clear=True)
    @patch("utils.firebase_config.load_dotenv")
    def test_missing_project_id_raises(self, mock_dotenv):
        """Test missing project ID raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FirebaseConfig()
        assert "FIREBASE_PROJECT_ID" in str(exc_info.value)

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project"
    }, clear=True)
    @patch("utils.firebase_config.load_dotenv")
    def test_missing_org_id_raises(self, mock_dotenv):
        """Test missing org ID raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FirebaseConfig()
        assert "ORG_ID" in str(exc_info.value)

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "INVALID_ORG"  # Contains uppercase
    }, clear=True)
    @patch("utils.firebase_config.load_dotenv")
    def test_invalid_org_id_format_raises(self, mock_dotenv):
        """Test invalid org ID format raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FirebaseConfig()
        assert "Invalid ORG_ID" in str(exc_info.value)

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "org_with_underscore"  # Contains underscore
    }, clear=True)
    @patch("utils.firebase_config.load_dotenv")
    def test_org_id_with_underscore_raises(self, mock_dotenv):
        """Test org ID with underscore raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            FirebaseConfig()
        assert "Invalid ORG_ID" in str(exc_info.value)


# =============================================================================
# auth_url property tests
# =============================================================================
class TestAuthUrl:
    """Tests for auth_url property"""

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_auth_url_value(self, mock_dotenv):
        """Test auth URL returns correct value"""
        config = FirebaseConfig()
        assert config.auth_url == "https://identitytoolkit.googleapis.com/v1/accounts"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "test-org"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_auth_url_is_https(self, mock_dotenv):
        """Test auth URL uses HTTPS"""
        config = FirebaseConfig()
        assert config.auth_url.startswith("https://")


# =============================================================================
# Valid org_id format tests
# =============================================================================
class TestValidOrgIdFormats:
    """Tests for valid org ID formats"""

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "lowercase"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_lowercase_org_id_valid(self, mock_dotenv):
        """Test lowercase org ID is valid"""
        config = FirebaseConfig()
        assert config.org_id == "lowercase"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "org-with-hyphens"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_hyphenated_org_id_valid(self, mock_dotenv):
        """Test hyphenated org ID is valid"""
        config = FirebaseConfig()
        assert config.org_id == "org-with-hyphens"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "org123"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_alphanumeric_org_id_valid(self, mock_dotenv):
        """Test alphanumeric org ID is valid"""
        config = FirebaseConfig()
        assert config.org_id == "org123"

    @patch.dict(os.environ, {
        "FIREBASE_API_KEY": "test_api_key",
        "FIREBASE_AUTH_DOMAIN": "test.firebaseapp.com",
        "FIREBASE_DATABASE_URL": "https://test.firebaseio.com",
        "FIREBASE_PROJECT_ID": "test-project",
        "ORG_ID": "my-org-123"
    })
    @patch("utils.firebase_config.load_dotenv")
    def test_mixed_format_org_id_valid(self, mock_dotenv):
        """Test mixed format org ID is valid"""
        config = FirebaseConfig()
        assert config.org_id == "my-org-123"



