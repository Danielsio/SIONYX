using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class KeyboardRestrictionServiceTests
{
    [Fact]
    public void Constructor_Default_ShouldBeEnabled()
    {
        var service = new KeyboardRestrictionService();
        service.Enabled.Should().BeTrue();
    }

    [Fact]
    public void Constructor_Disabled_ShouldNotBeEnabled()
    {
        var service = new KeyboardRestrictionService(enabled: false);
        service.Enabled.Should().BeFalse();
    }

    [Fact]
    public void IsActive_WhenNotStarted_ShouldBeFalse()
    {
        var service = new KeyboardRestrictionService();
        service.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Enabled_ShouldBeSettable()
    {
        var service = new KeyboardRestrictionService(enabled: false);
        service.Enabled = true;
        service.Enabled.Should().BeTrue();
    }

    [Fact]
    public void Stop_WithoutStart_ShouldNotThrow()
    {
        var service = new KeyboardRestrictionService();
        var act = () => service.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Start_WhenDisabled_ShouldNotActivate()
    {
        var service = new KeyboardRestrictionService(enabled: false);
        service.Start();
        service.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Dispose_ShouldNotThrow()
    {
        var service = new KeyboardRestrictionService();
        var act = () => service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_AfterStart_ShouldNotThrow()
    {
        var service = new KeyboardRestrictionService(enabled: false);
        service.Start();
        var act = () => service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void BlockedKeyPressed_Event_ShouldBeSubscribable()
    {
        var service = new KeyboardRestrictionService();
        string? blocked = null;
        service.BlockedKeyPressed += key => blocked = key;
        // Event should be subscribable without error
        service.Should().NotBeNull();
    }
}
