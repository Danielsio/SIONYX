namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Reconnect pacing for <see cref="SseListener"/> (pure logic, unit-testable).
/// Applies to error reconnects AND clean server closes — an instant reconnect
/// after a clean close hammers RTDB in a tight loop.
/// </summary>
public static class SseBackoff
{
    public const int InitialDelaySeconds = 1;
    public const int MaxDelaySeconds = 60;

    /// <summary>A connection must live this long before the backoff re-arms to the initial delay.</summary>
    public static readonly TimeSpan StableConnectionThreshold = TimeSpan.FromSeconds(30);

    public static int NextDelay(int currentSeconds) =>
        Math.Min(Math.Max(currentSeconds, InitialDelaySeconds) * 2, MaxDelaySeconds);

    /// <summary>
    /// Only a connection that stayed up a while earns a fresh backoff; a
    /// flapping server (accept → instant close) keeps doubling instead of
    /// re-arming a 1-second loop.
    /// </summary>
    public static bool ShouldReset(TimeSpan connectedDuration) => connectedDuration >= StableConnectionThreshold;
}
