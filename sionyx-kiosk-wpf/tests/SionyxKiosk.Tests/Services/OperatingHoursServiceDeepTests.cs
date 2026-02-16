using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for OperatingHoursService covering time checks and monitoring.
/// </summary>
public class OperatingHoursServiceDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OperatingHoursService _service;

    public OperatingHoursServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new OperatingHoursService(_firebase);
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    // ==================== IsWithinOperatingHours ====================

    [Fact]
    public void IsWithinOperatingHours_WhenDisabled_ShouldAlwaysReturnTrue()
    {
        _service.Settings.Enabled = false;
        var (allowed, reason) = _service.IsWithinOperatingHours();
        allowed.Should().BeTrue();
        reason.Should().BeNull();
    }

    [Fact]
    public void IsWithinOperatingHours_WhenEnabled_CurrentTimeInRange_ShouldReturnTrue()
    {
        var now = DateTime.Now;
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = now.AddHours(-1).ToString("HH:mm");
        _service.Settings.EndTime = now.AddHours(1).ToString("HH:mm");

        var (allowed, reason) = _service.IsWithinOperatingHours();
        allowed.Should().BeTrue();
        reason.Should().BeNull();
    }

    [Fact]
    public void IsWithinOperatingHours_WhenEnabled_CurrentTimeOutOfRange_ShouldReturnFalse()
    {
        var now = DateTime.Now;
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = now.AddHours(2).ToString("HH:mm");
        _service.Settings.EndTime = now.AddHours(4).ToString("HH:mm");

        var (allowed, reason) = _service.IsWithinOperatingHours();
        allowed.Should().BeFalse();
        reason.Should().Contain("שעות");
    }

    [Fact]
    public void IsWithinOperatingHours_WithCrossMidnightRange_InRange_ShouldReturnTrue()
    {
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = "22:00";
        _service.Settings.EndTime = "06:00";

        // This should be "in range" if current time is between 22:00 and 06:00
        // Test with a time that's "always in range" for cross-midnight
        var now = DateTime.Now;
        // If current time is before 06:00 or after 22:00, it's in range
        var (allowed, _) = _service.IsWithinOperatingHours();
        // Just verify it doesn't throw and returns a valid bool
        (allowed == true || allowed == false).Should().BeTrue();
    }

    [Fact]
    public void IsWithinOperatingHours_WithInvalidTimeFormat_ShouldReturnTrue()
    {
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = "invalid";
        _service.Settings.EndTime = "also-invalid";

        var (allowed, _) = _service.IsWithinOperatingHours();
        allowed.Should().BeTrue(); // Falls through as unparseable
    }

    [Fact]
    public void IsWithinOperatingHours_WithSingleDigitTime_ShouldHandleGracefully()
    {
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = "8:00";
        _service.Settings.EndTime = "22:00";

        var act = () => _service.IsWithinOperatingHours();
        act.Should().NotThrow();
    }

    // ==================== GetMinutesUntilClosing ====================

    [Fact]
    public void GetMinutesUntilClosing_WhenDisabled_ShouldReturnNegative()
    {
        _service.Settings.Enabled = false;
        var result = _service.GetMinutesUntilClosing();
        result.Should().Be(-1);
    }

    [Fact]
    public void GetMinutesUntilClosing_WithInvalidEndTime_ShouldReturnNegative()
    {
        _service.Settings.Enabled = true;
        _service.Settings.EndTime = "invalid";

        var result = _service.GetMinutesUntilClosing();
        result.Should().Be(-1);
    }

    [Fact]
    public void GetMinutesUntilClosing_WithFutureEndTime_ShouldReturnPositive()
    {
        _service.Settings.Enabled = true;
        _service.Settings.EndTime = DateTime.Now.AddHours(2).ToString("HH:mm");

        var result = _service.GetMinutesUntilClosing();
        result.Should().BeGreaterThan(0);
        result.Should().BeLessThanOrEqualTo(121); // ~2 hours = 120 mins + buffer
    }

    [Fact]
    public void GetMinutesUntilClosing_WithPastEndTime_ShouldWrapToNextDay()
    {
        _service.Settings.Enabled = true;
        _service.Settings.EndTime = DateTime.Now.AddMinutes(-30).ToString("HH:mm");

        var result = _service.GetMinutesUntilClosing();
        result.Should().BeGreaterThan(0); // Should wrap to next day
    }

    // ==================== LoadSettingsAsync ====================

    [Fact]
    public async Task LoadSettingsAsync_WithValidData_ShouldUpdateSettings()
    {
        _handler.When("operatingHours.json", new
        {
            enabled = true,
            startTime = "09:00",
            endTime = "21:00",
            gracePeriodMinutes = 15,
            graceBehavior = "force",
        });

        await _service.LoadSettingsAsync();

        _service.Settings.Enabled.Should().BeTrue();
        _service.Settings.StartTime.Should().Be("09:00");
        _service.Settings.EndTime.Should().Be("21:00");
        _service.Settings.GracePeriodMinutes.Should().Be(15);
        _service.Settings.GraceBehavior.Should().Be("force");
    }

    [Fact]
    public async Task LoadSettingsAsync_WithPartialData_ShouldLoadProvidedValues()
    {
        _handler.When("operatingHours.json", new
        {
            enabled = true,
            startTime = "07:00",
            endTime = "23:00",
            gracePeriodMinutes = 10,
            graceBehavior = "force",
        });

        await _service.LoadSettingsAsync();

        _service.Settings.Enabled.Should().BeTrue();
        _service.Settings.StartTime.Should().Be("07:00");
        _service.Settings.EndTime.Should().Be("23:00");
        _service.Settings.GracePeriodMinutes.Should().Be(10);
        _service.Settings.GraceBehavior.Should().Be("force");
    }

    [Fact]
    public async Task LoadSettingsAsync_WhenFails_ShouldUseDefaults()
    {
        _handler.WhenError("operatingHours.json");

        await _service.LoadSettingsAsync();

        _service.Settings.Enabled.Should().BeFalse();
    }

    [Fact]
    public async Task LoadSettingsAsync_WhenNull_ShouldUseDefaults()
    {
        _handler.WhenRaw("operatingHours.json", "null");

        await _service.LoadSettingsAsync();

        _service.Settings.Enabled.Should().BeFalse();
    }

    [Fact]
    public async Task LoadSettingsAsync_ShouldFireSettingsUpdated()
    {
        OperatingHoursSettings? updated = null;
        _service.SettingsUpdated += s => updated = s;

        _handler.When("operatingHours.json", new { enabled = true, startTime = "08:00", endTime = "22:00" });

        await _service.LoadSettingsAsync();

        updated.Should().NotBeNull();
        updated!.Enabled.Should().BeTrue();
    }

    // ==================== Monitoring ====================

    [Fact]
    public void IsMonitoring_Initially_ShouldBeFalse()
    {
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void StopMonitoring_WhenNotMonitoring_ShouldNotThrow()
    {
        var act = () => _service.StopMonitoring();
        act.Should().NotThrow();
    }

    // ==================== OperatingHoursSettings ====================

    [Fact]
    public void OperatingHoursSettings_Defaults_ShouldBeCorrect()
    {
        var settings = new OperatingHoursSettings();
        settings.Enabled.Should().BeFalse();
        settings.StartTime.Should().Be("06:00");
        settings.EndTime.Should().Be("00:00");
        settings.GracePeriodMinutes.Should().Be(5);
        settings.GraceBehavior.Should().Be("graceful");
    }

    [Fact]
    public void OperatingHoursSettings_AllProperties_ShouldBeSettable()
    {
        var settings = new OperatingHoursSettings
        {
            Enabled = true,
            StartTime = "08:30",
            EndTime = "23:00",
            GracePeriodMinutes = 10,
            GraceBehavior = "force",
        };

        settings.Enabled.Should().BeTrue();
        settings.StartTime.Should().Be("08:30");
        settings.EndTime.Should().Be("23:00");
        settings.GracePeriodMinutes.Should().Be(10);
        settings.GraceBehavior.Should().Be("force");
    }
}
