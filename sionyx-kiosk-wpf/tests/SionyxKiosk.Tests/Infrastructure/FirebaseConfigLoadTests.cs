using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for FirebaseConfig.LoadFromEnvironment by setting environment variables.
/// Uses [Collection] to avoid env var race conditions with FirebaseConfigFindEnvTests.
/// </summary>
[Collection("FirebaseConfig")]
public class FirebaseConfigLoadTests : IDisposable
{
    private readonly Dictionary<string, string?> _originalEnvVars = new();

    public FirebaseConfigLoadTests()
    {
        foreach (var key in new[] { "FIREBASE_API_KEY", "FIREBASE_AUTH_DOMAIN", "FIREBASE_DATABASE_URL", "FIREBASE_PROJECT_ID", "ORG_ID" })
        {
            _originalEnvVars[key] = Environment.GetEnvironmentVariable(key);
        }
    }

    public void Dispose()
    {
        foreach (var (key, value) in _originalEnvVars)
        {
            if (value == null)
                Environment.SetEnvironmentVariable(key, null);
            else
                Environment.SetEnvironmentVariable(key, value);
        }
    }

    private static FirebaseConfig LoadFromEnvironment()
    {
        var method = typeof(FirebaseConfig).GetMethod("LoadFromEnvironment", BindingFlags.NonPublic | BindingFlags.Static)!;
        return (FirebaseConfig)method.Invoke(null, null)!;
    }

    [Fact]
    public void LoadFromEnvironment_WithAllVarsSet_ShouldReturnConfig()
    {
        Environment.SetEnvironmentVariable("FIREBASE_API_KEY", "test-key");
        Environment.SetEnvironmentVariable("FIREBASE_AUTH_DOMAIN", "test.firebaseapp.com");
        Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", "https://test-db.firebaseio.com");
        Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", "test-project");
        Environment.SetEnvironmentVariable("ORG_ID", "test-org");

        var config = LoadFromEnvironment();

        config.ApiKey.Should().Be("test-key");
        config.AuthDomain.Should().Be("test.firebaseapp.com");
        config.DatabaseUrl.Should().Be("https://test-db.firebaseio.com");
        config.ProjectId.Should().Be("test-project");
        config.OrgId.Should().Be("test-org");
    }

    [Fact]
    public void LoadFromEnvironment_WithMissingApiKey_ShouldThrow()
    {
        // Whitespace prevents DotEnvLoader override (not null) but fails IsNullOrWhiteSpace
        Environment.SetEnvironmentVariable("FIREBASE_API_KEY", " ");
        Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", "https://test-db.firebaseio.com");
        Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", "test-project");
        Environment.SetEnvironmentVariable("ORG_ID", "test-org");

        var act = () => LoadFromEnvironment();
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*FIREBASE_API_KEY*");
    }

    [Fact]
    public void LoadFromEnvironment_WithNoAuthDomain_ShouldStillWork()
    {
        Environment.SetEnvironmentVariable("FIREBASE_API_KEY", "test-key");
        Environment.SetEnvironmentVariable("FIREBASE_AUTH_DOMAIN", " ");
        Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", "https://test-db.firebaseio.com");
        Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", "test-project");
        Environment.SetEnvironmentVariable("ORG_ID", "test-org");

        var config = LoadFromEnvironment();
        config.AuthDomain.Should().Match(d => d == null || string.IsNullOrWhiteSpace(d));
    }

    [Fact]
    public void LoadFromEnvironment_WithMissingOrgId_ShouldThrow()
    {
        Environment.SetEnvironmentVariable("FIREBASE_API_KEY", "test-key");
        Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", "https://test-db.firebaseio.com");
        Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", "test-project");
        Environment.SetEnvironmentVariable("ORG_ID", " ");

        var act = () => LoadFromEnvironment();
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*ORG_ID*");
    }

    [Fact]
    public void LoadFromEnvironment_WithInvalidOrgId_ShouldThrow()
    {
        Environment.SetEnvironmentVariable("FIREBASE_API_KEY", "test-key");
        Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", "https://test-db.firebaseio.com");
        Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", "test-project");
        Environment.SetEnvironmentVariable("ORG_ID", "INVALID ORG");

        var act = () => LoadFromEnvironment();
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*Invalid ORG_ID*");
    }
}
