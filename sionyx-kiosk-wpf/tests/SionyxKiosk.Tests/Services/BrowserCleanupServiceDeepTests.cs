using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for BrowserCleanupService covering cleanup operations.
/// </summary>
public class BrowserCleanupServiceDeepTests
{
    [Fact]
    public void Constructor_ShouldCreate()
    {
        var service = new BrowserCleanupService();
        service.Should().NotBeNull();
    }

    [Fact]
    public void CleanupAllBrowsers_ShouldReturnResultsWithExpectedKeys()
    {
        var service = new BrowserCleanupService();
        var result = service.CleanupAllBrowsers();

        result.Should().ContainKey("success");
        result.Should().ContainKey("chrome");
        result.Should().ContainKey("edge");
        result.Should().ContainKey("firefox");
    }

    [Fact]
    public void CleanupAllBrowsers_ChromeResult_ShouldHaveFilesDeletedKey()
    {
        var service = new BrowserCleanupService();
        var result = service.CleanupAllBrowsers();

        var chrome = (Dictionary<string, object>)result["chrome"];
        chrome.Should().ContainKey("success");
        chrome.Should().ContainKey("files_deleted");
    }

    [Fact]
    public void CleanupAllBrowsers_EdgeResult_ShouldHaveFilesDeletedKey()
    {
        var service = new BrowserCleanupService();
        var result = service.CleanupAllBrowsers();

        var edge = (Dictionary<string, object>)result["edge"];
        edge.Should().ContainKey("success");
        edge.Should().ContainKey("files_deleted");
    }

    [Fact]
    public void CleanupAllBrowsers_FirefoxResult_ShouldHaveFilesDeletedKey()
    {
        var service = new BrowserCleanupService();
        var result = service.CleanupAllBrowsers();

        var firefox = (Dictionary<string, object>)result["firefox"];
        firefox.Should().ContainKey("success");
        firefox.Should().ContainKey("files_deleted");
    }

    [Fact]
    public void CloseBrowsers_ShouldReturnResults()
    {
        var service = new BrowserCleanupService();
        var result = service.CloseBrowsers();

        result.Should().NotBeNull();
        result.Should().ContainKey("chrome");
        result.Should().ContainKey("edge");
        result.Should().ContainKey("firefox");
    }

    [Fact]
    public void CleanupWithBrowserClose_ShouldReturnResults()
    {
        var service = new BrowserCleanupService();
        var result = service.CleanupWithBrowserClose();

        result.Should().ContainKey("success");
        result.Should().ContainKey("chrome");
        result.Should().ContainKey("edge");
        result.Should().ContainKey("firefox");
        result.Should().ContainKey("browsers_closed");
    }

    [Fact]
    public void CloseBrowsers_AllBrowsersValues_ShouldBeBoolean()
    {
        var service = new BrowserCleanupService();
        var result = service.CloseBrowsers();

        foreach (var kvp in result)
        {
            (kvp.Value is bool).Should().BeTrue($"{kvp.Key} should be a boolean");
        }
    }
}
