using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Coverage tests for ProcessCleanupService.
/// These tests call real methods against the system; they verify execution without errors
/// and that returned result shapes are correct.
/// </summary>
public class ProcessCleanupServiceCoverageTests
{
    private readonly ProcessCleanupService _service;

    public ProcessCleanupServiceCoverageTests()
    {
        _service = new ProcessCleanupService();
    }

    // ==================== CONSTRUCTION ====================

    [Fact]
    public void Service_CanBeConstructed()
    {
        var svc = new ProcessCleanupService();
        svc.Should().NotBeNull();
    }

    // ==================== CleanupUserProcesses ====================

    [Fact]
    public void CleanupUserProcesses_DoesNotThrow()
    {
        var act = () => _service.CleanupUserProcesses();
        act.Should().NotThrow();
    }

    [Fact]
    public void CleanupUserProcesses_ReturnsNonNullDictionary()
    {
        var result = _service.CleanupUserProcesses();
        result.Should().NotBeNull();
    }

    [Fact]
    public void CleanupUserProcesses_ReturnsExpectedKeys()
    {
        var result = _service.CleanupUserProcesses();
        result.Should().ContainKey("success");
        result.Should().ContainKey("closed_count");
        result.Should().ContainKey("failed_count");
        result.Should().ContainKey("closed_processes");
        result.Should().ContainKey("failed_processes");
    }

    [Fact]
    public void CleanupUserProcesses_SuccessIsBoolean()
    {
        var result = _service.CleanupUserProcesses();
        result["success"].Should().BeOfType<bool>();
    }

    [Fact]
    public void CleanupUserProcesses_ClosedCountIsInt()
    {
        var result = _service.CleanupUserProcesses();
        result["closed_count"].Should().BeOfType<int>();
    }

    [Fact]
    public void CleanupUserProcesses_FailedCountIsInt()
    {
        var result = _service.CleanupUserProcesses();
        result["failed_count"].Should().BeOfType<int>();
    }

    [Fact]
    public void CleanupUserProcesses_ClosedProcessesIsListOfString()
    {
        var result = _service.CleanupUserProcesses();
        result["closed_processes"].Should().BeAssignableTo<IEnumerable<string>>();
    }

    [Fact]
    public void CleanupUserProcesses_FailedProcessesIsListOfString()
    {
        var result = _service.CleanupUserProcesses();
        result["failed_processes"].Should().BeAssignableTo<IEnumerable<string>>();
    }

    [Fact]
    public void CleanupUserProcesses_SuccessTrueWhenNoFailures()
    {
        var result = _service.CleanupUserProcesses();
        var failedCount = (int)result["failed_count"];
        var success = (bool)result["success"];
        if (failedCount == 0)
            success.Should().BeTrue();
    }

    [Fact]
    public void CleanupUserProcesses_ClosedAndFailedCountsAreNonNegative()
    {
        var result = _service.CleanupUserProcesses();
        ((int)result["closed_count"]).Should().BeGreaterThanOrEqualTo(0);
        ((int)result["failed_count"]).Should().BeGreaterThanOrEqualTo(0);
    }

    // ==================== CloseBrowsersOnly ====================

    [Fact]
    public void CloseBrowsersOnly_DoesNotThrow()
    {
        var act = () => _service.CloseBrowsersOnly();
        act.Should().NotThrow();
    }

    [Fact]
    public void CloseBrowsersOnly_ReturnsNonNullDictionary()
    {
        var result = _service.CloseBrowsersOnly();
        result.Should().NotBeNull();
    }

    [Fact]
    public void CloseBrowsersOnly_ReturnsExpectedKeys()
    {
        var result = _service.CloseBrowsersOnly();
        result.Should().ContainKey("success");
        result.Should().ContainKey("closed_count");
    }

    [Fact]
    public void CloseBrowsersOnly_SuccessIsAlwaysTrue()
    {
        var result = _service.CloseBrowsersOnly();
        result["success"].Should().Be(true);
    }

    [Fact]
    public void CloseBrowsersOnly_ClosedCountIsNonNegative()
    {
        var result = _service.CloseBrowsersOnly();
        ((int)result["closed_count"]).Should().BeGreaterThanOrEqualTo(0);
    }

    // ==================== MULTIPLE INVOCATIONS ====================

    [Fact]
    public void CleanupUserProcesses_CanBeCalledMultipleTimes()
    {
        var act = () =>
        {
            _service.CleanupUserProcesses();
            _service.CleanupUserProcesses();
        };
        act.Should().NotThrow();
    }

    [Fact]
    public void CloseBrowsersOnly_CanBeCalledMultipleTimes()
    {
        var act = () =>
        {
            _service.CloseBrowsersOnly();
            _service.CloseBrowsersOnly();
        };
        act.Should().NotThrow();
    }
}
