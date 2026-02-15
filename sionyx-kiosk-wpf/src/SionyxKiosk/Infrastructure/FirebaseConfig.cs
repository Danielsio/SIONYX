using System.IO;
using System.Text.RegularExpressions;

namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Firebase configuration loaded from Windows Registry (production) or environment variables (development).
/// </summary>
public sealed class FirebaseConfig
{
    public string ApiKey { get; }
    public string? AuthDomain { get; }
    public string DatabaseUrl { get; }
    public string ProjectId { get; }
    public string OrgId { get; }

    /// <summary>Firebase Auth REST API base URL.</summary>
    public string AuthUrl => "https://identitytoolkit.googleapis.com/v1/accounts";

    private FirebaseConfig(string apiKey, string? authDomain, string databaseUrl, string projectId, string orgId)
    {
        ApiKey = apiKey;
        AuthDomain = authDomain;
        DatabaseUrl = databaseUrl;
        ProjectId = projectId;
        OrgId = orgId;
    }

    /// <summary>
    /// Load configuration from the appropriate source (registry or environment).
    /// Validates all required fields.
    /// </summary>
    public static FirebaseConfig Load()
    {
        return RegistryConfig.IsProduction()
            ? LoadFromRegistry()
            : LoadFromEnvironment();
    }

    private static FirebaseConfig LoadFromRegistry()
    {
        var config = RegistryConfig.GetAllConfig();

        var apiKey = config["ApiKey"];
        var authDomain = config["AuthDomain"];
        var databaseUrl = config["DatabaseUrl"];
        var projectId = config["ProjectId"];
        var orgId = config["OrgId"];

        return CreateAndValidate(apiKey, authDomain, databaseUrl, projectId, orgId, "registry");
    }

    private static FirebaseConfig LoadFromEnvironment()
    {
        // Load .env file if it exists
        var envPath = FindEnvFile();
        if (envPath != null)
            DotEnvLoader.Load(envPath);

        var apiKey = Environment.GetEnvironmentVariable("FIREBASE_API_KEY");
        var authDomain = Environment.GetEnvironmentVariable("FIREBASE_AUTH_DOMAIN");
        var databaseUrl = Environment.GetEnvironmentVariable("FIREBASE_DATABASE_URL");
        var projectId = Environment.GetEnvironmentVariable("FIREBASE_PROJECT_ID");
        var orgId = Environment.GetEnvironmentVariable("ORG_ID");

        return CreateAndValidate(apiKey, authDomain, databaseUrl, projectId, orgId, ".env");
    }

    private static FirebaseConfig CreateAndValidate(
        string? apiKey, string? authDomain, string? databaseUrl,
        string? projectId, string? orgId, string source)
    {
        if (string.IsNullOrWhiteSpace(apiKey))
            throw new InvalidOperationException($"FIREBASE_API_KEY missing in {source}");
        if (string.IsNullOrWhiteSpace(databaseUrl))
            throw new InvalidOperationException($"FIREBASE_DATABASE_URL missing in {source}");
        if (string.IsNullOrWhiteSpace(projectId))
            throw new InvalidOperationException($"FIREBASE_PROJECT_ID missing in {source}");
        if (string.IsNullOrWhiteSpace(orgId))
            throw new InvalidOperationException(
                $"ORG_ID missing in {source}\n" +
                "This identifies your organization in the database.\n" +
                "Example: ORG_ID=myorg");

        if (!Regex.IsMatch(orgId, @"^[a-z0-9-]+$"))
            throw new InvalidOperationException(
                $"Invalid ORG_ID: '{orgId}'\n" +
                "Must contain only lowercase letters, numbers, and hyphens.\n" +
                "Example: myorg, tech-lab, university-cs");

        return new FirebaseConfig(apiKey, authDomain, databaseUrl, projectId, orgId);
    }

    private static string? FindEnvFile()
    {
        // Walk up from the executable to find .env
        var dir = AppDomain.CurrentDomain.BaseDirectory;

        // Try project root patterns
        for (var i = 0; i < 5; i++)
        {
            var envPath = Path.Combine(dir, ".env");
            if (File.Exists(envPath)) return envPath;
            var parent = Directory.GetParent(dir);
            if (parent == null) break;
            dir = parent.FullName;
        }

        return null;
    }
}
