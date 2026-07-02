using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// SSE reconnect pacing (M-2): backoff must apply to clean server closes too,
/// and only a connection that stayed up re-arms the fast retry.
/// </summary>
public class SseBackoffTests
{
    [Theory]
    [InlineData(1, 2)]
    [InlineData(2, 4)]
    [InlineData(32, 60)]
    [InlineData(60, 60)]
    public void NextDelay_DoublesUpToTheCap(int current, int expected)
    {
        SseBackoff.NextDelay(current).Should().Be(expected);
    }

    [Fact]
    public void NextDelay_RecoversFromInvalidState()
    {
        SseBackoff.NextDelay(0).Should().Be(2);
        SseBackoff.NextDelay(-5).Should().Be(2);
    }

    [Fact]
    public void ShortLivedConnection_DoesNotResetBackoff()
    {
        // A flapping server (accept → instant close) must keep doubling.
        SseBackoff.ShouldReset(TimeSpan.FromSeconds(1)).Should().BeFalse();
        SseBackoff.ShouldReset(TimeSpan.FromSeconds(29)).Should().BeFalse();
    }

    [Fact]
    public void StableConnection_ResetsBackoff()
    {
        SseBackoff.ShouldReset(TimeSpan.FromSeconds(30)).Should().BeTrue();
        SseBackoff.ShouldReset(TimeSpan.FromMinutes(10)).Should().BeTrue();
    }
}
