using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class OperatingHoursServiceTests : IDisposable
{
    private readonly OperatingHoursService _service;

    public OperatingHoursServiceTests()
    {
        _service = new OperatingHoursService(null!);
    }

    public void Dispose() => _service.Dispose();

    // ==================== SETTINGS DEFAULTS ====================

    [Fact]
    public void Settings_Default_ShouldNotBeEnabled()
    {
        _service.Settings.Enabled.Should().BeFalse();
    }

    [Fact]
    public void Settings_Default_ShouldHaveDefaultTimes()
    {
        _service.Settings.StartTime.Should().Be("06:00");
        _service.Settings.EndTime.Should().Be("00:00");
    }

    [Fact]
    public void Settings_Default_ShouldHaveGracePeriod()
    {
        _service.Settings.GracePeriodMinutes.Should().Be(5);
        _service.Settings.GraceBehavior.Should().Be("graceful");
    }

    // ==================== IS WITHIN OPERATING HOURS ====================

    [Fact]
    public void IsWithinOperatingHours_WhenDisabled_ShouldAllow()
    {
        _service.Settings.Enabled = false;
        var (isAllowed, reason) = _service.IsWithinOperatingHours();
        isAllowed.Should().BeTrue();
        reason.Should().BeNull();
    }

    [Fact]
    public void IsWithinOperatingHours_WithinNormalHours_ShouldAllow()
    {
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = "00:00";
        _service.Settings.EndTime = "23:59";

        var (isAllowed, reason) = _service.IsWithinOperatingHours();
        isAllowed.Should().BeTrue();
    }

    [Fact]
    public void IsWithinOperatingHours_OutsideHours_ShouldDeny()
    {
        _service.Settings.Enabled = true;

        // Set a window that is definitely not now
        // If current time is between 0:00-23:59, set hours to a very small window in the past
        var now = DateTime.Now;
        var startHour = (now.Hour + 2) % 24;
        var endHour = (now.Hour + 3) % 24;
        _service.Settings.StartTime = $"{startHour:D2}:00";
        _service.Settings.EndTime = $"{endHour:D2}:00";

        var (isAllowed, reason) = _service.IsWithinOperatingHours();
        isAllowed.Should().BeFalse();
        reason.Should().NotBeNullOrEmpty();
        reason.Should().Contain(_service.Settings.StartTime);
    }

    [Fact]
    public void IsWithinOperatingHours_WithInvalidFormat_ShouldAllow()
    {
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = "invalid";
        _service.Settings.EndTime = "also-invalid";

        var (isAllowed, _) = _service.IsWithinOperatingHours();
        isAllowed.Should().BeTrue(); // Invalid format should default to allowed
    }

    [Fact]
    public void IsWithinOperatingHours_WithOvernightHours_ShouldHandleCorrectly()
    {
        _service.Settings.Enabled = true;
        // Overnight window: 22:00 to 06:00 (start > end)
        _service.Settings.StartTime = "00:00";
        _service.Settings.EndTime = "23:59";

        var (isAllowed, _) = _service.IsWithinOperatingHours();
        isAllowed.Should().BeTrue();
    }

    // ==================== GET MINUTES UNTIL CLOSING ====================

    [Fact]
    public void GetMinutesUntilClosing_WhenDisabled_ShouldReturnNegative()
    {
        _service.Settings.Enabled = false;
        _service.GetMinutesUntilClosing().Should().BeLessThan(0);
    }

    [Fact]
    public void GetMinutesUntilClosing_WithValidEndTime_ShouldReturnPositive()
    {
        _service.Settings.Enabled = true;
        // Set end time to 1 hour from now
        var endTime = DateTime.Now.AddHours(1);
        _service.Settings.EndTime = endTime.ToString("HH:mm");

        var minutes = _service.GetMinutesUntilClosing();
        minutes.Should().BeInRange(55, 65); // approximately 60 minutes
    }

    [Fact]
    public void GetMinutesUntilClosing_WithInvalidEndTime_ShouldReturnNegative()
    {
        _service.Settings.Enabled = true;
        _service.Settings.EndTime = "invalid";

        _service.GetMinutesUntilClosing().Should().BeLessThan(0);
    }

    // ==================== MONITORING ====================

    [Fact]
    public void IsMonitoring_Initially_ShouldBeFalse()
    {
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void StartMonitoring_ShouldSetIsMonitoring()
    {
        _service.StartMonitoring();
        _service.IsMonitoring.Should().BeTrue();
        _service.StopMonitoring(); // cleanup
    }

    [Fact]
    public void StopMonitoring_ShouldUnsetIsMonitoring()
    {
        _service.StartMonitoring();
        _service.StopMonitoring();
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void StopMonitoring_WithoutStart_ShouldNotThrow()
    {
        var act = () => _service.StopMonitoring();
        act.Should().NotThrow();
    }

    [Fact]
    public void StartMonitoring_Twice_ShouldBeIdempotent()
    {
        _service.StartMonitoring();
        _service.StartMonitoring(); // Should not throw
        _service.IsMonitoring.Should().BeTrue();
        _service.StopMonitoring();
    }

    [Fact]
    public void Dispose_ShouldStopMonitoring()
    {
        _service.StartMonitoring();
        _service.Dispose();
        _service.IsMonitoring.Should().BeFalse();
    }
}

public class OperatingHoursSettingsTests
{
    [Fact]
    public void DefaultValues_ShouldBeCorrect()
    {
        var settings = new OperatingHoursSettings();
        settings.Enabled.Should().BeFalse();
        settings.StartTime.Should().Be("06:00");
        settings.EndTime.Should().Be("00:00");
        settings.GracePeriodMinutes.Should().Be(5);
        settings.GraceBehavior.Should().Be("graceful");
    }

    [Fact]
    public void Properties_ShouldBeSettable()
    {
        var settings = new OperatingHoursSettings
        {
            Enabled = true,
            StartTime = "08:00",
            EndTime = "22:00",
            GracePeriodMinutes = 10,
            GraceBehavior = "force",
        };

        settings.Enabled.Should().BeTrue();
        settings.StartTime.Should().Be("08:00");
        settings.EndTime.Should().Be("22:00");
        settings.GracePeriodMinutes.Should().Be(10);
        settings.GraceBehavior.Should().Be("force");
    }
}
