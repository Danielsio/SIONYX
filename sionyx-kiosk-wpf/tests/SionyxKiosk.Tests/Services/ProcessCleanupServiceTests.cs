using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ProcessCleanupServiceTests
{
    [Fact]
    public void Constructor_ShouldNotThrow()
    {
        var service = new ProcessCleanupService();
        service.Should().NotBeNull();
    }

    [Fact]
    public void CleanupUserProcesses_ShouldNotThrow()
    {
        // Should not throw even if no processes match
        var service = new ProcessCleanupService();
        var act = () => service.CleanupUserProcesses();
        act.Should().NotThrow();
    }
}
