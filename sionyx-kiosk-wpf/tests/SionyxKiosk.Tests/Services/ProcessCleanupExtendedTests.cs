using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ProcessCleanupExtendedTests
{
    [Fact]
    public void CloseBrowsersOnly_ShouldReturnResults()
    {
        var service = new ProcessCleanupService();
        var results = service.CloseBrowsersOnly();

        results.Should().ContainKey("success");
        results.Should().ContainKey("closed_count");
    }

    [Fact]
    public void CleanupUserProcesses_ShouldReturnAllExpectedKeys()
    {
        var service = new ProcessCleanupService();
        var results = service.CleanupUserProcesses();

        results.Should().ContainKey("success");
        results.Should().ContainKey("closed_count");
        results.Should().ContainKey("failed_count");
        results.Should().ContainKey("closed_processes");
        results.Should().ContainKey("failed_processes");
    }

    [Fact]
    public void CleanupUserProcesses_ClosedProcesses_ShouldBeList()
    {
        var service = new ProcessCleanupService();
        var results = service.CleanupUserProcesses();

        results["closed_processes"].Should().BeOfType<List<string>>();
        results["failed_processes"].Should().BeOfType<List<string>>();
    }
}
