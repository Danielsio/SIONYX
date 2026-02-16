using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class OperatingHoursServiceExtendedTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OperatingHoursService _service;

    public OperatingHoursServiceExtendedTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new OperatingHoursService(_firebase);
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    [Fact]
    public async Task LoadSettingsAsync_WithValidData_ShouldPopulateSettings()
    {
        _handler.When("operatingHours.json", new
        {
            enabled = true,
            startTime = "08:00",
            endTime = "22:00",
            gracePeriodMinutes = 10,
            graceBehavior = "force",
        });

        await _service.LoadSettingsAsync();

        _service.Settings.Enabled.Should().BeTrue();
        _service.Settings.StartTime.Should().Be("08:00");
        _service.Settings.EndTime.Should().Be("22:00");
        _service.Settings.GracePeriodMinutes.Should().Be(10);
        _service.Settings.GraceBehavior.Should().Be("force");
    }

    [Fact]
    public async Task LoadSettingsAsync_WhenFails_ShouldUseDefaults()
    {
        _handler.WhenError("operatingHours.json");

        await _service.LoadSettingsAsync();

        _service.Settings.Enabled.Should().BeFalse();
        _service.Settings.StartTime.Should().Be("06:00");
    }

    [Fact]
    public async Task LoadSettingsAsync_WhenNull_ShouldUseDefaults()
    {
        _handler.WhenRaw("operatingHours.json", "null");

        await _service.LoadSettingsAsync();

        _service.Settings.Enabled.Should().BeFalse();
    }

    [Fact]
    public async Task LoadSettingsAsync_ShouldFireSettingsUpdatedEvent()
    {
        OperatingHoursSettings? updated = null;
        _service.SettingsUpdated += s => updated = s;

        _handler.When("operatingHours.json", new
        {
            enabled = true,
            startTime = "09:00",
            endTime = "21:00",
        });

        await _service.LoadSettingsAsync();

        updated.Should().NotBeNull();
    }

    [Fact]
    public void HoursEndingSoon_Event_ShouldBeSubscribable()
    {
        int? minutes = null;
        _service.HoursEndingSoon += m => minutes = m;
        _service.Should().NotBeNull();
    }

    [Fact]
    public void HoursEnded_Event_ShouldBeSubscribable()
    {
        string? behavior = null;
        _service.HoursEnded += b => behavior = b;
        _service.Should().NotBeNull();
    }

    [Fact]
    public void IsWithinOperatingHours_CurrentTimeInRange_ShouldReturnTrue()
    {
        var now = DateTime.Now;
        _service.Settings.Enabled = true;
        _service.Settings.StartTime = now.AddHours(-1).ToString("HH:mm");
        _service.Settings.EndTime = now.AddHours(1).ToString("HH:mm");

        var (isAllowed, reason) = _service.IsWithinOperatingHours();
        isAllowed.Should().BeTrue();
        reason.Should().BeNull();
    }
}
