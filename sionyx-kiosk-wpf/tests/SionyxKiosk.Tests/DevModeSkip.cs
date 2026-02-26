namespace SionyxKiosk.Tests;

/// <summary>
/// Use instead of [Fact] on destructive tests (process killing, file deletion, etc.).
/// When DEVMODE=true (or DEVMODE=1) is set in the environment, these tests are skipped.
/// In CI (GitHub Actions) DEVMODE is not set, so all tests run normally.
/// </summary>
public class DestructiveFactAttribute : FactAttribute
{
    public DestructiveFactAttribute()
    {
        var val = Environment.GetEnvironmentVariable("DEVMODE");
        var isDevMode = string.Equals(val, "true", StringComparison.OrdinalIgnoreCase)
                     || string.Equals(val, "1", StringComparison.OrdinalIgnoreCase);

        if (isDevMode)
            Skip = "Skipped in DEVMODE (destructive test)";
    }
}
