using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

[Trait("Category", "Destructive")]
public class ProcessCleanupServiceTests
{
    [DestructiveFact]
    public void Constructor_ShouldNotThrow()
    {
        var service = new ProcessCleanupService();
        service.Should().NotBeNull();
    }

    [DestructiveFact]
    public void CleanupUserProcesses_ShouldNotThrow()
    {
        // Should not throw even if no processes match
        var service = new ProcessCleanupService();
        var act = () => service.CleanupUserProcesses();
        act.Should().NotThrow();
    }
}
