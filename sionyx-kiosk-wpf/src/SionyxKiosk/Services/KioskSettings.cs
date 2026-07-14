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

    public static KioskSettings Defaults { get; } = new();
}
