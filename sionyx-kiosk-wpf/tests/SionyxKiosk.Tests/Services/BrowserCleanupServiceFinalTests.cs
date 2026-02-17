using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Coverage tests for BrowserCleanupService: path helpers, static arrays,
/// cleanup methods that don't require running browsers.
/// </summary>
public class BrowserCleanupServiceFinalTests
{
    private readonly BrowserCleanupService _service = new();

    // ==================== CLEANUP ALL BROWSERS ====================

    [Fact]
    public void CleanupAllBrowsers_ShouldReturnSuccessKey()
    {
        var results = _service.CleanupAllBrowsers();
        results.Should().ContainKey("success");
        results["success"].Should().Be(true);
    }

    [Fact]
    public void CleanupAllBrowsers_ShouldReturnChromeResult()
    {
        var results = _service.CleanupAllBrowsers();
        results.Should().ContainKey("chrome");
        results["chrome"].Should().BeOfType<Dictionary<string, object>>();
    }

    [Fact]
    public void CleanupAllBrowsers_ShouldReturnEdgeResult()
    {
        var results = _service.CleanupAllBrowsers();
        results.Should().ContainKey("edge");
        results["edge"].Should().BeOfType<Dictionary<string, object>>();
    }

    [Fact]
    public void CleanupAllBrowsers_ShouldReturnFirefoxResult()
    {
        var results = _service.CleanupAllBrowsers();
        results.Should().ContainKey("firefox");
        results["firefox"].Should().BeOfType<Dictionary<string, object>>();
    }

    [Fact]
    public void CleanupAllBrowsers_EachBrowser_ShouldHaveFilesDeletedKey()
    {
        var results = _service.CleanupAllBrowsers();

        foreach (var browser in new[] { "chrome", "edge", "firefox" })
        {
            var browserResult = (Dictionary<string, object>)results[browser];
            browserResult.Should().ContainKey("files_deleted");
            browserResult.Should().ContainKey("success");
        }
    }

    // ==================== CLOSE BROWSERS ====================

    [Fact]
    public void CloseBrowsers_ShouldReturnDictionaryOfResults()
    {
        var results = _service.CloseBrowsers();
        results.Should().NotBeNull();
        // Each entry should be true (closed or wasn't running)
        foreach (var kvp in results)
        {
            kvp.Value.Should().BeTrue();
        }
    }

    // ==================== PATH HELPERS (via reflection) ====================

    [Fact]
    public void GetChromePaths_ShouldReturnNonEmptyArray()
    {
        var method = typeof(BrowserCleanupService).GetMethod("GetChromePaths",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var paths = (string[])method.Invoke(null, null)!;
        paths.Should().NotBeEmpty();
        paths[0].Should().Contain("Chrome");
    }

    [Fact]
    public void GetEdgePaths_ShouldReturnNonEmptyArray()
    {
        var method = typeof(BrowserCleanupService).GetMethod("GetEdgePaths",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var paths = (string[])method.Invoke(null, null)!;
        paths.Should().NotBeEmpty();
        paths[0].Should().Contain("Edge");
    }

    [Fact]
    public void GetFirefoxProfilesPath_ShouldReturnValidPath()
    {
        var method = typeof(BrowserCleanupService).GetMethod("GetFirefoxProfilesPath",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var path = (string)method.Invoke(null, null)!;
        path.Should().Contain("Firefox");
        path.Should().Contain("Profiles");
    }

    // ==================== TRY DELETE (non-existent paths) ====================

    [Fact]
    public void TryDeleteFileOrDir_WithNonExistentPath_ShouldReturnZero()
    {
        var method = typeof(BrowserCleanupService).GetMethod("TryDeleteFileOrDir",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var errors = new List<string>();
        var result = (int)method.Invoke(null, new object[] { @"C:\__nonexistent_path__\file.txt", "Test", errors })!;
        result.Should().Be(0);
        errors.Should().BeEmpty();
    }

    // ==================== CHROMIUM FILES ARRAY ====================

    [Fact]
    public void ChromiumFiles_ShouldContainCookies()
    {
        var field = typeof(BrowserCleanupService).GetField("ChromiumFiles",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var files = (string[])field.GetValue(null)!;
        files.Should().Contain("Cookies");
    }

    [Fact]
    public void ChromiumFiles_ShouldContainLoginData()
    {
        var field = typeof(BrowserCleanupService).GetField("ChromiumFiles",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var files = (string[])field.GetValue(null)!;
        files.Should().Contain("Login Data");
    }

    [Fact]
    public void FirefoxFiles_ShouldContainCookiesSqlite()
    {
        var field = typeof(BrowserCleanupService).GetField("FirefoxFiles",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var files = (string[])field.GetValue(null)!;
        files.Should().Contain("cookies.sqlite");
    }

    // ==================== FIND CHROMIUM PROFILES ====================

    [Fact]
    public void FindChromiumProfiles_WithEmptyDir_ShouldReturnEmpty()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"chromium_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        try
        {
            var method = typeof(BrowserCleanupService).GetMethod("FindChromiumProfiles",
                BindingFlags.NonPublic | BindingFlags.Static)!;
            var profiles = (string[])method.Invoke(null, new object[] { tempDir })!;
            profiles.Should().BeEmpty();
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void FindChromiumProfiles_WithDefaultProfile_ShouldReturnIt()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"chromium_test_{Guid.NewGuid():N}");
        var defaultDir = Path.Combine(tempDir, "Default");
        Directory.CreateDirectory(defaultDir);
        try
        {
            var method = typeof(BrowserCleanupService).GetMethod("FindChromiumProfiles",
                BindingFlags.NonPublic | BindingFlags.Static)!;
            var profiles = (string[])method.Invoke(null, new object[] { tempDir })!;
            profiles.Should().HaveCount(1);
            profiles[0].Should().Contain("Default");
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }
}
