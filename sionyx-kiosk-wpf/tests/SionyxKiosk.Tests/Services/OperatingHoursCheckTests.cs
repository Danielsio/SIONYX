using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Tests for OperatingHoursService.CheckOperatingHours via reflection.
/// This private method is called by the DispatcherTimer, so we test it directly.
/// </summary>
public class OperatingHoursCheckTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OperatingHoursService _service;
    private readonly MethodInfo _checkMethod;

    public OperatingHoursCheckTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new OperatingHoursService(_firebase);
        _checkMethod = typeof(OperatingHoursService)
            .GetMethod("CheckOperatingHours", BindingFlags.NonPublic | BindingFlags.Instance)!;
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    [Fact]
    public void CheckOperatingHours_WhenDisabled_ShouldDoNothing()
    {
        _service.Settings.Enabled = false;
        var act = () => _checkMethod.Invoke(_service, null);
        act.Should().NotThrow();
    }

    [Fact]
    public void CheckOperatingHours_WhenOutsideHours_ShouldFireHoursEnded()
    {
        string? behavior = null;
        _service.HoursEnded += b => behavior = b;

        _service.Settings.Enabled = true;
        _service.Settings.StartTime = DateTime.Now.AddHours(3).ToString("HH:mm");
        _service.Settings.EndTime = DateTime.Now.AddHours(5).ToString("HH:mm");
        _service.Settings.GraceBehavior = "force";

        _checkMethod.Invoke(_service, null);

        behavior.Should().Be("force");
    }

    [Fact]
    public void CheckOperatingHours_WhenInsideHoursWithinGrace_ShouldFireHoursEndingSoon()
    {
        int? minutes = null;
        _service.HoursEndingSoon += m => minutes = m;

        _service.Settings.Enabled = true;
        _service.Settings.StartTime = DateTime.Now.AddHours(-8).ToString("HH:mm");
        _service.Settings.EndTime = DateTime.Now.AddMinutes(3).ToString("HH:mm"); // 3 min until close
        _service.Settings.GracePeriodMinutes = 10; // Grace period is 10 min, we're within it

        _checkMethod.Invoke(_service, null);

        minutes.Should().NotBeNull();
        minutes.Should().BeLessThanOrEqualTo(10);
    }

    [Fact]
    public void CheckOperatingHours_WhenInsideHoursNotInGrace_ShouldNotFireEvents()
    {
        int? minutes = null;
        string? behavior = null;
        _service.HoursEndingSoon += m => minutes = m;
        _service.HoursEnded += b => behavior = b;

        _service.Settings.Enabled = true;
        _service.Settings.StartTime = DateTime.Now.AddHours(-4).ToString("HH:mm");
        _service.Settings.EndTime = DateTime.Now.AddHours(4).ToString("HH:mm"); // 4 hours until close
        _service.Settings.GracePeriodMinutes = 10;

        _checkMethod.Invoke(_service, null);

        minutes.Should().BeNull();
        behavior.Should().BeNull();
    }

    [Fact]
    public void CheckOperatingHours_GraceWarning_ShouldOnlyFireOnce()
    {
        var fireCount = 0;
        _service.HoursEndingSoon += _ => fireCount++;

        _service.Settings.Enabled = true;
        _service.Settings.StartTime = DateTime.Now.AddHours(-8).ToString("HH:mm");
        _service.Settings.EndTime = DateTime.Now.AddMinutes(3).ToString("HH:mm");
        _service.Settings.GracePeriodMinutes = 10;

        _checkMethod.Invoke(_service, null);
        _checkMethod.Invoke(_service, null);
        _checkMethod.Invoke(_service, null);

        fireCount.Should().Be(1); // Should only warn once
    }

    [Fact]
    public void TryParseTime_WithValidTime_ShouldParse()
    {
        var method = typeof(OperatingHoursService)
            .GetMethod("TryParseTime", BindingFlags.NonPublic | BindingFlags.Static)!;

        var args = new object[] { "14:30", TimeSpan.Zero };
        var result = (bool)method.Invoke(null, args)!;

        result.Should().BeTrue();
        ((TimeSpan)args[1]).Should().Be(new TimeSpan(14, 30, 0));
    }

    [Fact]
    public void TryParseTime_WithInvalidFormat_ShouldReturnFalse()
    {
        var method = typeof(OperatingHoursService)
            .GetMethod("TryParseTime", BindingFlags.NonPublic | BindingFlags.Static)!;

        var args = new object[] { "invalid", TimeSpan.Zero };
        var result = (bool)method.Invoke(null, args)!;
        result.Should().BeFalse();
    }

    [Fact]
    public void TryParseTime_WithSinglePart_ShouldReturnFalse()
    {
        var method = typeof(OperatingHoursService)
            .GetMethod("TryParseTime", BindingFlags.NonPublic | BindingFlags.Static)!;

        var args = new object[] { "1430", TimeSpan.Zero };
        var result = (bool)method.Invoke(null, args)!;
        result.Should().BeFalse();
    }

    [Fact]
    public void TryParseTime_WithNonNumeric_ShouldReturnFalse()
    {
        var method = typeof(OperatingHoursService)
            .GetMethod("TryParseTime", BindingFlags.NonPublic | BindingFlags.Static)!;

        var args = new object[] { "ab:cd", TimeSpan.Zero };
        var result = (bool)method.Invoke(null, args)!;
        result.Should().BeFalse();
    }
}
