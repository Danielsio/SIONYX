using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ProcessRestrictionServiceTests
{
    [Fact]
    public void StartStop_ShouldNotThrow()
    {
        var service = new ProcessRestrictionService();

        var startAct = () => service.Start();
        startAct.Should().NotThrow();

        var stopAct = () => service.Stop();
        stopAct.Should().NotThrow();
    }

    [Fact]
    public void Start_ThenStop_ShouldBeIdempotent()
    {
        var service = new ProcessRestrictionService();

        service.Start();
        service.Start(); // Double start should be safe
        service.Stop();
        service.Stop(); // Double stop should be safe
    }
}
