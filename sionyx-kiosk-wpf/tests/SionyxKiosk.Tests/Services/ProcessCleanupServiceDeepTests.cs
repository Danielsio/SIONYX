using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for ProcessCleanupService covering method return structures.
/// Note: Actual process killing is system-dependent and can't be reliably unit tested.
/// </summary>
public class ProcessCleanupServiceDeepTests
{
    [Fact]
    public void CleanupUserProcesses_ShouldReturnExpectedStructure()
    {
        var service = new ProcessCleanupService();
        var result = service.CleanupUserProcesses();

        result.Should().ContainKey("success");
        result.Should().ContainKey("closed_count");
        result.Should().ContainKey("failed_count");
        result.Should().ContainKey("closed_processes");
        result.Should().ContainKey("failed_processes");
    }

    [Fact]
    public void CleanupUserProcesses_ClosedCount_ShouldBeNonNegative()
    {
        var service = new ProcessCleanupService();
        var result = service.CleanupUserProcesses();

        ((int)result["closed_count"]).Should().BeGreaterThanOrEqualTo(0);
        ((int)result["failed_count"]).Should().BeGreaterThanOrEqualTo(0);
    }

    [Fact]
    public void CleanupUserProcesses_ProcessLists_ShouldBeListOfStrings()
    {
        var service = new ProcessCleanupService();
        var result = service.CleanupUserProcesses();

        result["closed_processes"].Should().BeOfType<List<string>>();
        result["failed_processes"].Should().BeOfType<List<string>>();
    }

    [Fact]
    public void CloseBrowsersOnly_ShouldReturnExpectedStructure()
    {
        var service = new ProcessCleanupService();
        var result = service.CloseBrowsersOnly();

        result.Should().ContainKey("success");
        result.Should().ContainKey("closed_count");
    }

    [Fact]
    public void CloseBrowsersOnly_ClosedCount_ShouldBeNonNegative()
    {
        var service = new ProcessCleanupService();
        var result = service.CloseBrowsersOnly();

        ((int)result["closed_count"]).Should().BeGreaterThanOrEqualTo(0);
    }

    [Fact]
    public void CloseBrowsersOnly_Success_ShouldBeTrue()
    {
        var service = new ProcessCleanupService();
        var result = service.CloseBrowsersOnly();

        ((bool)result["success"]).Should().BeTrue();
    }
}
