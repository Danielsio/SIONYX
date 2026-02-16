using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for KeyboardRestrictionService properties and non-P/Invoke behavior.
/// </summary>
public class KeyboardRestrictionDeepTests
{
    [Fact]
    public void Constructor_DefaultEnabled_ShouldBeTrue()
    {
        using var service = new KeyboardRestrictionService();
        service.Enabled.Should().BeTrue();
    }

    [Fact]
    public void Constructor_ExplicitlyDisabled_ShouldBeFalse()
    {
        using var service = new KeyboardRestrictionService(enabled: false);
        service.Enabled.Should().BeFalse();
    }

    [Fact]
    public void IsActive_Initially_ShouldBeFalse()
    {
        using var service = new KeyboardRestrictionService();
        // IsActive requires both hook handle and enabled
        service.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Start_WhenDisabled_ShouldNotInstallHook()
    {
        using var service = new KeyboardRestrictionService(enabled: false);
        service.Start();
        service.IsActive.Should().BeFalse();
    }

    [Fact]
    public void Stop_WhenNotStarted_ShouldNotThrow()
    {
        using var service = new KeyboardRestrictionService();
        var act = () => service.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_ShouldNotThrow()
    {
        var service = new KeyboardRestrictionService();
        var act = () => service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_MultipleTimes_ShouldNotThrow()
    {
        var service = new KeyboardRestrictionService();
        service.Dispose();
        var act = () => service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Enabled_CanBeToggled()
    {
        using var service = new KeyboardRestrictionService(enabled: true);
        service.Enabled.Should().BeTrue();

        service.Enabled = false;
        service.Enabled.Should().BeFalse();

        service.Enabled = true;
        service.Enabled.Should().BeTrue();
    }

    [Fact]
    public void BlockedKeyPressed_Event_ShouldBeSubscribable()
    {
        using var service = new KeyboardRestrictionService();
        service.BlockedKeyPressed += _ => { };
        service.Should().NotBeNull();
    }

    [Fact]
    public void Start_ThenStop_ShouldNotThrow()
    {
        using var service = new KeyboardRestrictionService(enabled: false);
        service.Start(); // No-op since disabled
        service.Stop();
        service.IsActive.Should().BeFalse();
    }
}
