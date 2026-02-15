"""
Tests for BrowserCleanupService

Testing Strategy:
- Mock file system operations (don't actually delete user's browser data!)
- Test path discovery logic
- Test error handling for permission errors and missing files
- Test browser detection
"""

from unittest.mock import Mock, patch

import pytest

from services.browser_cleanup_service import BrowserCleanupService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def cleanup_service():
    """Create a BrowserCleanupService instance."""
    return BrowserCleanupService()


@pytest.fixture
def mock_paths(tmp_path):
    """Create mock browser paths for testing."""
    # Create Chrome-like structure
    chrome_path = tmp_path / "Google" / "Chrome" / "User Data" / "Default"
    chrome_path.mkdir(parents=True)
    (chrome_path / "Cookies").touch()
    (chrome_path / "Login Data").touch()
    (chrome_path / "History").touch()

    # Create Edge-like structure
    edge_path = tmp_path / "Microsoft" / "Edge" / "User Data" / "Default"
    edge_path.mkdir(parents=True)
    (edge_path / "Cookies").touch()

    # Create Firefox-like structure
    firefox_path = tmp_path / "Mozilla" / "Firefox" / "Profiles" / "abc123.default"
    firefox_path.mkdir(parents=True)
    (firefox_path / "cookies.sqlite").touch()
    (firefox_path / "logins.json").touch()

    return {
        "chrome": tmp_path / "Google" / "Chrome" / "User Data",
        "edge": tmp_path / "Microsoft" / "Edge" / "User Data",
        "firefox": tmp_path / "Mozilla" / "Firefox" / "Profiles",
    }


# =============================================================================
# Test Initialization
# =============================================================================


class TestBrowserCleanupServiceInit:
    """Tests for service initialization."""

    def test_creates_instance(self, cleanup_service):
        """Test service can be instantiated."""
        assert cleanup_service is not None
        assert isinstance(cleanup_service, BrowserCleanupService)

    def test_has_cleanup_results_dict(self, cleanup_service):
        """Test service has cleanup results tracking."""
        assert hasattr(cleanup_service, "_cleanup_results")
        assert isinstance(cleanup_service._cleanup_results, dict)


# =============================================================================
# Test Path Discovery
# =============================================================================


class TestFindChromiumProfiles:
    """Tests for _find_chromium_profiles method."""

    def test_finds_default_profile(self, cleanup_service, tmp_path):
        """Test finds Default profile directory."""
        default = tmp_path / "Default"
        default.mkdir()

        profiles = cleanup_service._find_chromium_profiles(tmp_path)

        assert len(profiles) == 1
        assert profiles[0] == default

    def test_finds_numbered_profiles(self, cleanup_service, tmp_path):
        """Test finds Profile 1, Profile 2, etc."""
        (tmp_path / "Default").mkdir()
        (tmp_path / "Profile 1").mkdir()
        (tmp_path / "Profile 2").mkdir()

        profiles = cleanup_service._find_chromium_profiles(tmp_path)

        assert len(profiles) == 3

    def test_ignores_non_profile_directories(self, cleanup_service, tmp_path):
        """Test ignores directories that aren't profiles."""
        (tmp_path / "Default").mkdir()
        (tmp_path / "Crashpad").mkdir()
        (tmp_path / "GrShaderCache").mkdir()

        profiles = cleanup_service._find_chromium_profiles(tmp_path)

        assert len(profiles) == 1

    def test_handles_missing_path(self, cleanup_service, tmp_path):
        """Test handles non-existent path gracefully."""
        nonexistent = tmp_path / "nonexistent"

        profiles = cleanup_service._find_chromium_profiles(nonexistent)

        assert len(profiles) == 0


# =============================================================================
# Test Chrome Cleanup
# =============================================================================


class TestChromeCleanup:
    """Tests for Chrome cleanup functionality."""

    def test_cleanup_deletes_cookie_files(self, cleanup_service, mock_paths):
        """Test Chrome cleanup deletes cookie files."""
        # Patch the Chrome paths to use our mock
        with patch.object(
            BrowserCleanupService, "CHROME_PATHS", [mock_paths["chrome"]]
        ):
            result = cleanup_service._cleanup_chrome()

        assert result["success"] is True
        assert result["files_deleted"] >= 1

        # Verify files were deleted
        assert not (mock_paths["chrome"] / "Default" / "Cookies").exists()

    def test_cleanup_handles_missing_chrome(self, cleanup_service, tmp_path):
        """Test handles missing Chrome installation."""
        nonexistent = tmp_path / "nonexistent"

        with patch.object(BrowserCleanupService, "CHROME_PATHS", [nonexistent]):
            result = cleanup_service._cleanup_chrome()

        assert result["success"] is True
        assert result["files_deleted"] == 0

    def test_cleanup_handles_permission_error(self, cleanup_service, mock_paths):
        """Test handles permission errors gracefully."""
        with patch.object(
            BrowserCleanupService, "CHROME_PATHS", [mock_paths["chrome"]]
        ):
            with patch("pathlib.Path.unlink") as mock_unlink:
                mock_unlink.side_effect = PermissionError("Access denied")
                result = cleanup_service._cleanup_chrome()

        assert result["success"] is False
        assert "Permission denied" in result.get("error", "")


# =============================================================================
# Test Edge Cleanup
# =============================================================================


class TestEdgeCleanup:
    """Tests for Edge cleanup functionality."""

    def test_cleanup_deletes_edge_files(self, cleanup_service, mock_paths):
        """Test Edge cleanup deletes cookie files."""
        with patch.object(BrowserCleanupService, "EDGE_PATHS", [mock_paths["edge"]]):
            result = cleanup_service._cleanup_edge()

        assert result["success"] is True
        assert not (mock_paths["edge"] / "Default" / "Cookies").exists()


# =============================================================================
# Test Firefox Cleanup
# =============================================================================


class TestFirefoxCleanup:
    """Tests for Firefox cleanup functionality."""

    def test_cleanup_deletes_firefox_files(self, cleanup_service, mock_paths):
        """Test Firefox cleanup deletes cookie files."""
        with patch.object(
            BrowserCleanupService, "FIREFOX_PATHS", [mock_paths["firefox"]]
        ):
            result = cleanup_service._cleanup_firefox()

        assert result["success"] is True
        assert result["files_deleted"] >= 1

    def test_cleanup_handles_missing_firefox(self, cleanup_service, tmp_path):
        """Test handles missing Firefox installation."""
        nonexistent = tmp_path / "nonexistent"

        with patch.object(BrowserCleanupService, "FIREFOX_PATHS", [nonexistent]):
            result = cleanup_service._cleanup_firefox()

        assert result["success"] is True
        assert result["files_deleted"] == 0


# =============================================================================
# Test Full Cleanup
# =============================================================================


class TestCleanupAllBrowsers:
    """Tests for cleanup_all_browsers method."""

    def test_cleanup_all_returns_results_for_each_browser(self, cleanup_service):
        """Test cleanup returns results for Chrome, Edge, Firefox."""
        with patch.object(
            cleanup_service, "_cleanup_chrome", return_value={"success": True}
        ):
            with patch.object(
                cleanup_service, "_cleanup_edge", return_value={"success": True}
            ):
                with patch.object(
                    cleanup_service, "_cleanup_firefox", return_value={"success": True}
                ):
                    result = cleanup_service.cleanup_all_browsers()

        assert "chrome" in result
        assert "edge" in result
        assert "firefox" in result
        assert result["success"] is True

    def test_cleanup_all_reports_errors(self, cleanup_service):
        """Test cleanup reports errors from individual browsers."""
        with patch.object(
            cleanup_service, "_cleanup_chrome", return_value={"success": True}
        ):
            with patch.object(
                cleanup_service,
                "_cleanup_edge",
                return_value={"success": False, "error": "Permission denied"},
            ):
                with patch.object(
                    cleanup_service, "_cleanup_firefox", return_value={"success": True}
                ):
                    result = cleanup_service.cleanup_all_browsers()

        assert result["success"] is False
        assert len(result["errors"]) > 0


# =============================================================================
# Test Browser Detection
# =============================================================================


class TestIsBrowserRunning:
    """Tests for is_browser_running method."""

    def test_detects_chrome_running(self, cleanup_service):
        """Test detects Chrome running."""
        mock_result = Mock()
        mock_result.stdout = '"chrome.exe","12345","Console","1","123,456 K"'

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service.is_browser_running("chrome")

        assert result is True

    def test_detects_browser_not_running(self, cleanup_service):
        """Test detects browser not running."""
        mock_result = Mock()
        mock_result.stdout = '"System","0","Console","0","0 K"'

        with patch("subprocess.run", return_value=mock_result):
            result = cleanup_service.is_browser_running("chrome")

        assert result is False

    def test_handles_subprocess_error(self, cleanup_service):
        """Test handles subprocess error gracefully."""
        with patch("subprocess.run", side_effect=Exception("Error")):
            result = cleanup_service.is_browser_running("chrome")

        assert result is False


# =============================================================================
# Test Close Browsers
# =============================================================================


class TestCloseBrowsers:
    """Tests for close_browsers method."""

    def test_closes_running_browsers(self, cleanup_service):
        """Test closes browsers that are running."""
        with patch.object(cleanup_service, "is_browser_running", return_value=True):
            with patch("subprocess.run") as mock_run:
                result = cleanup_service.close_browsers()

        assert mock_run.called
        assert result["chrome"] is True

    def test_skips_browsers_not_running(self, cleanup_service):
        """Test skips browsers that aren't running."""
        with patch.object(cleanup_service, "is_browser_running", return_value=False):
            with patch("subprocess.run"):
                result = cleanup_service.close_browsers()

        # Should not call taskkill if browser isn't running
        assert result["chrome"] is True


# =============================================================================
# Test Cleanup With Browser Close
# =============================================================================


class TestCleanupWithBrowserClose:
    """Tests for cleanup_with_browser_close method."""

    def test_closes_browsers_then_cleans(self, cleanup_service):
        """Test closes browsers before cleanup."""
        close_results = {"chrome": True, "edge": True, "firefox": True}
        cleanup_results = {
            "success": True,
            "chrome": {"success": True},
            "edge": {"success": True},
            "firefox": {"success": True},
            "errors": [],
        }

        with patch.object(
            cleanup_service, "close_browsers", return_value=close_results
        ):
            with patch.object(
                cleanup_service, "cleanup_all_browsers", return_value=cleanup_results
            ):
                with patch("time.sleep"):  # Skip the sleep
                    result = cleanup_service.cleanup_with_browser_close()

        assert result["success"] is True
        assert "browsers_closed" in result
        assert result["browsers_closed"] == close_results


# =============================================================================
# Test File Lists
# =============================================================================


class TestFileLists:
    """Tests for file lists constants."""

    def test_chromium_files_include_cookies(self, cleanup_service):
        """Test Chromium files list includes Cookies."""
        assert "Cookies" in BrowserCleanupService.CHROMIUM_FILES_TO_DELETE

    def test_chromium_files_include_login_data(self, cleanup_service):
        """Test Chromium files list includes Login Data."""
        assert "Login Data" in BrowserCleanupService.CHROMIUM_FILES_TO_DELETE

    def test_firefox_files_include_cookies(self, cleanup_service):
        """Test Firefox files list includes cookies.sqlite."""
        assert "cookies.sqlite" in BrowserCleanupService.FIREFOX_FILES_TO_DELETE

    def test_firefox_files_include_logins(self, cleanup_service):
        """Test Firefox files list includes logins.json."""
        assert "logins.json" in BrowserCleanupService.FIREFOX_FILES_TO_DELETE
