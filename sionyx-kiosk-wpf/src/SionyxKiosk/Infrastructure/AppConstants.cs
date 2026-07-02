namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Global application constants and configuration.
/// </summary>
public static class AppConstants
{
    /// <summary>Application display name (brand).</summary>
    public const string AppName = "SIONYX";

    /// <summary>Default admin exit hotkey combination.</summary>
    public const string AdminExitHotkeyDefault = "Ctrl+Alt+Space";

    /// <summary>Fallback password for local development only. Production reads from registry.</summary>
    private const string DefaultAdminPassword = "dev-exit";

    /// <summary>
    /// Returned when a production kiosk has no AdminExitPassword configured.
    /// Contains NUL characters, so no keyboard input can ever equal it — the
    /// exit prompt always denies instead of accepting the public dev constant.
    /// </summary>
    public const string ExitDeniedSentinel = "\0SIONYX_EXIT_DENIED\0";

    /// <summary>
    /// Load admin exit password from configuration.
    /// Production (registry present): registry value or DENY (fail closed).
    /// Development: environment variable or the dev default.
    /// </summary>
    public static string GetAdminExitPassword() =>
        ResolveAdminExitPassword(
            RegistryConfig.IsProduction(),
            RegistryConfig.ReadValue("AdminExitPassword"),
            Environment.GetEnvironmentVariable("ADMIN_EXIT_PASSWORD"));

    /// <summary>
    /// Pure decision logic (unit-testable). A production kiosk with a
    /// missing/empty registry password FAILS CLOSED: falling back to the
    /// "dev-exit" constant (visible in this public repo) would let anyone
    /// exit the lockdown on a misconfigured install.
    /// </summary>
    public static string ResolveAdminExitPassword(bool isProduction, string? registryPassword, string? envPassword)
    {
        if (isProduction)
            return string.IsNullOrEmpty(registryPassword) ? ExitDeniedSentinel : registryPassword;

        if (!string.IsNullOrEmpty(envPassword))
            return envPassword;

        return DefaultAdminPassword;
    }
}
