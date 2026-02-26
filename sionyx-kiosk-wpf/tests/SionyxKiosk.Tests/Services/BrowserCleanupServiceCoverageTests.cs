using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Coverage tests for BrowserCleanupService.
/// These tests call real methods against the system; they verify execution without errors
/// and that returned result shapes are correct.
/// </summary>
[Trait("Category", "Destructive")]
public class BrowserCleanupServiceCoverageTests
{
    private readonly BrowserCleanupService _service;

    public BrowserCleanupServiceCoverageTests()
    {
        _service = new BrowserCleanupService();
    }

    // ==================== CONSTRUCTION ====================

    [DestructiveFact]
    public void Service_CanBeConstructed()
    {
        var svc = new BrowserCleanupService();
        svc.Should().NotBeNull();
    }

    // ==================== CloseBrowsers ====================

    [DestructiveFact]
    public void CloseBrowsers_DoesNotThrow()
    {
        var act = () => _service.CloseBrowsers();
        act.Should().NotThrow();
    }

    [DestructiveFact]
    public void CloseBrowsers_ReturnsNonNullDictionary()
    {
        var result = _service.CloseBrowsers();
        result.Should().NotBeNull();
    }

    [DestructiveFact]
    public void CloseBrowsers_ReturnsExpectedKeys()
    {
        var result = _service.CloseBrowsers();
        result.Should().ContainKey("chrome");
        result.Should().ContainKey("edge");
        result.Should().ContainKey("firefox");
    }

    [DestructiveFact]
    public void CloseBrowsers_ValuesAreBoolean()
    {
        var result = _service.CloseBrowsers();
        ((object)result["chrome"]).Should().BeOfType<bool>();
        ((object)result["edge"]).Should().BeOfType<bool>();
        ((object)result["firefox"]).Should().BeOfType<bool>();
    }

    [DestructiveFact]
    public void CloseBrowsers_ReturnsDictionaryWithThreeEntries()
    {
        var result = _service.CloseBrowsers();
        result.Should().HaveCount(3);
    }

    // ==================== CleanupAllBrowsers ====================

    [DestructiveFact]
    public void CleanupAllBrowsers_DoesNotThrow()
    {
        var act = () => _service.CleanupAllBrowsers();
        act.Should().NotThrow();
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_ReturnsNonNullDictionary()
    {
        var result = _service.CleanupAllBrowsers();
        result.Should().NotBeNull();
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_ReturnsExpectedKeys()
    {
        var result = _service.CleanupAllBrowsers();
        result.Should().ContainKey("success");
        result.Should().ContainKey("chrome");
        result.Should().ContainKey("edge");
        result.Should().ContainKey("firefox");
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_SuccessIsBoolean()
    {
        var result = _service.CleanupAllBrowsers();
        result["success"].Should().BeOfType<bool>();
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_ChromeResultHasExpectedShape()
    {
        var result = _service.CleanupAllBrowsers();
        var chrome = result["chrome"].Should().BeAssignableTo<Dictionary<string, object>>().Subject;
        chrome.Should().ContainKey("success");
        chrome.Should().ContainKey("files_deleted");
        chrome["success"].Should().BeOfType<bool>();
        chrome["files_deleted"].Should().BeOfType<int>();
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_EdgeResultHasExpectedShape()
    {
        var result = _service.CleanupAllBrowsers();
        var edge = result["edge"].Should().BeAssignableTo<Dictionary<string, object>>().Subject;
        edge.Should().ContainKey("success");
        edge.Should().ContainKey("files_deleted");
        edge["success"].Should().BeOfType<bool>();
        edge["files_deleted"].Should().BeOfType<int>();
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_FirefoxResultHasExpectedShape()
    {
        var result = _service.CleanupAllBrowsers();
        var firefox = result["firefox"].Should().BeAssignableTo<Dictionary<string, object>>().Subject;
        firefox.Should().ContainKey("success");
        firefox.Should().ContainKey("files_deleted");
        firefox["success"].Should().BeOfType<bool>();
        firefox["files_deleted"].Should().BeOfType<int>();
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_FilesDeletedIsNonNegative()
    {
        var result = _service.CleanupAllBrowsers();
        ((int)((Dictionary<string, object>)result["chrome"])["files_deleted"]).Should().BeGreaterThanOrEqualTo(0);
        ((int)((Dictionary<string, object>)result["edge"])["files_deleted"]).Should().BeGreaterThanOrEqualTo(0);
        ((int)((Dictionary<string, object>)result["firefox"])["files_deleted"]).Should().BeGreaterThanOrEqualTo(0);
    }

    // ==================== CleanupWithBrowserClose ====================

    [DestructiveFact]
    public void CleanupWithBrowserClose_DoesNotThrow()
    {
        var act = () => _service.CleanupWithBrowserClose();
        act.Should().NotThrow();
    }

    [DestructiveFact]
    public void CleanupWithBrowserClose_ReturnsNonNullDictionary()
    {
        var result = _service.CleanupWithBrowserClose();
        result.Should().NotBeNull();
    }

    [DestructiveFact]
    public void CleanupWithBrowserClose_ReturnsExpectedKeys()
    {
        var result = _service.CleanupWithBrowserClose();
        result.Should().ContainKey("success");
        result.Should().ContainKey("chrome");
        result.Should().ContainKey("edge");
        result.Should().ContainKey("firefox");
        result.Should().ContainKey("browsers_closed");
    }

    [DestructiveFact]
    public void CleanupWithBrowserClose_BrowsersClosedHasExpectedShape()
    {
        var result = _service.CleanupWithBrowserClose();
        var browsersClosed = result["browsers_closed"].Should().BeAssignableTo<Dictionary<string, bool>>().Subject;
        browsersClosed.Should().ContainKey("chrome");
        browsersClosed.Should().ContainKey("edge");
        browsersClosed.Should().ContainKey("firefox");
    }

    [DestructiveFact]
    public void CleanupWithBrowserClose_IncludesCleanupResults()
    {
        var result = _service.CleanupWithBrowserClose();
        var chrome = (Dictionary<string, object>)result["chrome"];
        chrome.Should().ContainKey("success");
        chrome.Should().ContainKey("files_deleted");
    }

    // ==================== MULTIPLE INVOCATIONS ====================

    [DestructiveFact]
    public void CloseBrowsers_CanBeCalledMultipleTimes()
    {
        var act = () =>
        {
            _service.CloseBrowsers();
            _service.CloseBrowsers();
        };
        act.Should().NotThrow();
    }

    [DestructiveFact]
    public void CleanupAllBrowsers_CanBeCalledMultipleTimes()
    {
        var act = () =>
        {
            _service.CleanupAllBrowsers();
            _service.CleanupAllBrowsers();
        };
        act.Should().NotThrow();
    }

    [DestructiveFact]
    public void CleanupWithBrowserClose_CanBeCalledMultipleTimes()
    {
        var act = () =>
        {
            _service.CleanupWithBrowserClose();
            _service.CleanupWithBrowserClose();
        };
        act.Should().NotThrow();
    }
}
