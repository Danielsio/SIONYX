using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class BrowserCleanupServiceTests
{
    private readonly BrowserCleanupService _service = new();

    [Fact]
    public void CleanupAllBrowsers_ShouldReturnResults()
    {
        var results = _service.CleanupAllBrowsers();

        results.Should().ContainKey("success");
        results.Should().ContainKey("chrome");
        results.Should().ContainKey("edge");
        results.Should().ContainKey("firefox");
    }

    [Fact]
    public void CleanupAllBrowsers_ChromeResult_ShouldHaveExpectedKeys()
    {
        var results = _service.CleanupAllBrowsers();
        var chrome = (Dictionary<string, object>)results["chrome"];
        chrome.Should().ContainKey("success");
        chrome.Should().ContainKey("files_deleted");
    }

    [Fact]
    public void CleanupAllBrowsers_FirefoxResult_ShouldHaveExpectedKeys()
    {
        var results = _service.CleanupAllBrowsers();
        var firefox = (Dictionary<string, object>)results["firefox"];
        firefox.Should().ContainKey("success");
        firefox.Should().ContainKey("files_deleted");
    }

    [Fact]
    public void CloseBrowsers_ShouldReturnResults()
    {
        var results = _service.CloseBrowsers();
        results.Should().NotBeNull();
        // Should have results for each browser
    }

    [Fact]
    public void CleanupWithBrowserClose_ShouldReturnResults()
    {
        var results = _service.CleanupWithBrowserClose();
        results.Should().ContainKey("browsers_closed");
        results.Should().ContainKey("chrome");
        results.Should().ContainKey("edge");
        results.Should().ContainKey("firefox");
    }
}
