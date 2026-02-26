using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for ProcessCleanupService covering method return structures.
/// Note: Actual process killing is system-dependent and can't be reliably unit tested.
/// </summary>
[Trait("Category", "Destructive")]
public class ProcessCleanupServiceDeepTests
{
    [DestructiveFact]
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

    [DestructiveFact]
    public void CleanupUserProcesses_ClosedCount_ShouldBeNonNegative()
    {
        var service = new ProcessCleanupService();
        var result = service.CleanupUserProcesses();

        ((int)result["closed_count"]).Should().BeGreaterThanOrEqualTo(0);
        ((int)result["failed_count"]).Should().BeGreaterThanOrEqualTo(0);
    }

    [DestructiveFact]
    public void CleanupUserProcesses_ProcessLists_ShouldBeListOfStrings()
    {
        var service = new ProcessCleanupService();
        var result = service.CleanupUserProcesses();

        result["closed_processes"].Should().BeOfType<List<string>>();
        result["failed_processes"].Should().BeOfType<List<string>>();
    }

    [DestructiveFact]
    public void CloseBrowsersOnly_ShouldReturnExpectedStructure()
    {
        var service = new ProcessCleanupService();
        var result = service.CloseBrowsersOnly();

        result.Should().ContainKey("success");
        result.Should().ContainKey("closed_count");
    }

    [DestructiveFact]
    public void CloseBrowsersOnly_ClosedCount_ShouldBeNonNegative()
    {
        var service = new ProcessCleanupService();
        var result = service.CloseBrowsersOnly();

        ((int)result["closed_count"]).Should().BeGreaterThanOrEqualTo(0);
    }

    [DestructiveFact]
    public void CloseBrowsersOnly_Success_ShouldBeTrue()
    {
        var service = new ProcessCleanupService();
        var result = service.CloseBrowsersOnly();

        ((bool)result["success"]).Should().BeTrue();
    }
}
