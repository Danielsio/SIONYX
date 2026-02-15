using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ForceLogoutServiceTests
{
    [Fact]
    public void Constructor_ShouldNotThrow()
    {
        var service = new ForceLogoutService(null!);
        service.Should().NotBeNull();
    }

    [Fact]
    public void StopListening_WithoutStart_ShouldNotThrow()
    {
        var service = new ForceLogoutService(null!);

        var act = () => service.StopListening();
        act.Should().NotThrow();
    }
}
