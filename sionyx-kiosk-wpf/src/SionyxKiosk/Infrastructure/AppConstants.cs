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

    /// <summary>Default fallback password (only used if neither registry nor env provides one).</summary>
    private const string DefaultAdminPassword = "sionyx2025";

    /// <summary>
    /// Load admin exit password from configuration.
    /// Priority: Registry -> Environment variable -> Default fallback.
    /// </summary>
    public static string GetAdminExitPassword()
    {
        // Production: read from registry
        if (RegistryConfig.IsProduction())
        {
            var password = RegistryConfig.ReadValue("AdminExitPassword");
            if (!string.IsNullOrEmpty(password))
                return password;
        }

        // Development: read from environment
        var envPassword = Environment.GetEnvironmentVariable("ADMIN_EXIT_PASSWORD");
        if (!string.IsNullOrEmpty(envPassword))
            return envPassword;

        return DefaultAdminPassword;
    }
}
