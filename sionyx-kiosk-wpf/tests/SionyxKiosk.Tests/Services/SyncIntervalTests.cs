using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Sync cadence resolution (M-3): configurable, shorter default, clamped so a
/// bad value can neither hammer the Worker nor stop syncing.
/// </summary>
public class SyncIntervalTests
{
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("not-a-number")]
    public void Unconfigured_UsesTheDefault(string? configured)
    {
        SessionService.ResolveSyncIntervalSeconds(configured)
            .Should().Be(SessionService.DefaultSyncIntervalSeconds);
    }

    [Fact]
    public void DefaultIsShorterThanTheOldFixedMinute()
    {
        SessionService.DefaultSyncIntervalSeconds.Should().BeLessThan(60);
    }

    [Theory]
    [InlineData("45", 45)]
    [InlineData("10", 10)]
    [InlineData("300", 300)]
    public void ConfiguredValue_IsUsed(string configured, int expected)
    {
        SessionService.ResolveSyncIntervalSeconds(configured).Should().Be(expected);
    }

    [Theory]
    [InlineData("1", 10)]     // too fast → clamped up
    [InlineData("0", 10)]
    [InlineData("-5", 10)]
    [InlineData("9999", 300)] // too slow → clamped down
    public void OutOfRangeValues_AreClamped(string configured, int expected)
    {
        SessionService.ResolveSyncIntervalSeconds(configured).Should().Be(expected);
    }
}
