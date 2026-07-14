namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Decides whether an entered admin-exit password unlocks the kiosk.
///
/// Two sources, in order:
///   1. The org's REMOTE password, set from the web console. It is stored
///      encrypted server-side; the kiosk never sees it, it only asks the backend
///      "is this it?". When the org has configured one, it is authoritative.
///   2. The LOCAL password provisioned by the installer (registry). This is the
///      break-glass path when the backend is unreachable, and stays fail-closed:
///      a production kiosk with no password configured returns a sentinel that
///      no keyboard input can match (see AppConstants).
/// </summary>
public static class ExitPasswordVerifier
{
    /// <param name="entered">What the operator typed.</param>
    /// <param name="remoteConfigured">The org has a remote password set.</param>
    /// <param name="remoteValid">The backend says `entered` matches the remote password.</param>
    /// <param name="localPassword">The installer-provisioned password (or the deny sentinel).</param>
    public static bool IsAllowed(string entered, bool remoteConfigured, bool remoteValid, string localPassword)
    {
        // A configured remote password is the source of truth — an admin who
        // rotates it in the console must invalidate the old one everywhere.
        if (remoteConfigured) return remoteValid;

        // No remote password (or the backend could not be reached): the locally
        // provisioned password is the only way out. Fail-closed when unset.
        return !string.IsNullOrEmpty(entered) && entered == localPassword;
    }
}
