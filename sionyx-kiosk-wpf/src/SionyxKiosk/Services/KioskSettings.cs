namespace SionyxKiosk.Services;

/// <summary>
/// Kiosk behaviour an admin can change from the web console
/// (organizations/$orgId/metadata/settings). Everything has a safe default so a
/// kiosk whose org has no settings configured behaves exactly as before.
/// </summary>
public sealed class KioskSettings
{
    /// <summary>Sender name shown for admin chat messages. Empty → the kiosk's generic fallback.</summary>
    public string DisplayName { get; init; } = "";

    /// <summary>Whether the saved-card ("keva") one-click flow is offered. Off unless enabled.</summary>
    public bool SaveCardEnabled { get; init; }

    /// <summary>
    /// When true, a user may not start a session until an admin has marked their
    /// phone verified in the web console. Off unless enabled.
    /// </summary>
    public bool RequirePhoneVerification { get; init; }

    /// <summary>Org-supplied background image for the kiosk's login screen (empty = none).</summary>
    public string BackgroundUrl { get; init; } = "";

    /// <summary>Whether the org turned the custom background on.</summary>
    public bool BackgroundEnabled { get; init; }

    public static KioskSettings Defaults { get; } = new();

    /// <summary>
    /// A branded background is shown only when the org enabled it AND supplied a
    /// usable absolute http(s) URL. Anything else falls back to the built-in look,
    /// so a bad value can never leave the kiosk with a broken screen.
    /// </summary>
    public static bool ShouldShowBackground(bool enabled, string? url) =>
        enabled &&
        !string.IsNullOrWhiteSpace(url) &&
        Uri.TryCreate(url, UriKind.Absolute, out var uri) &&
        (uri.Scheme == Uri.UriSchemeHttp || uri.Scheme == Uri.UriSchemeHttps);

    /// <summary>
    /// Whether this user is blocked from starting a session. Pure and testable:
    /// blocked only when the org requires verification AND the user is not verified.
    /// </summary>
    public static bool IsSessionBlocked(bool requireVerification, bool userVerified) =>
        requireVerification && !userVerified;

    /// <summary>Convenience: does THIS settings object call for a branded background?</summary>
    public bool HasUsableBackground => ShouldShowBackground(BackgroundEnabled, BackgroundUrl);
}
