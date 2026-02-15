using System.IO;

namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Simple .env file loader. Reads KEY=VALUE pairs and sets them as environment variables.
/// Replaces the Python python-dotenv dependency.
/// </summary>
public static class DotEnvLoader
{
    /// <summary>
    /// Load a .env file and set its values as environment variables.
    /// Existing environment variables are NOT overwritten.
    /// </summary>
    public static void Load(string filePath)
    {
        if (!File.Exists(filePath)) return;

        foreach (var line in File.ReadAllLines(filePath))
        {
            var trimmed = line.Trim();

            // Skip empty lines and comments
            if (string.IsNullOrEmpty(trimmed) || trimmed.StartsWith('#'))
                continue;

            var separatorIndex = trimmed.IndexOf('=');
            if (separatorIndex < 0) continue;

            var key = trimmed[..separatorIndex].Trim();
            var value = trimmed[(separatorIndex + 1)..].Trim();

            // Remove surrounding quotes if present
            if (value.Length >= 2 &&
                ((value.StartsWith('"') && value.EndsWith('"')) ||
                 (value.StartsWith('\'') && value.EndsWith('\''))))
            {
                value = value[1..^1];
            }

            // Don't override existing environment variables
            if (Environment.GetEnvironmentVariable(key) == null)
            {
                Environment.SetEnvironmentVariable(key, value);
            }
        }
    }
}
