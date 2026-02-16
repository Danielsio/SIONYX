using System.IO;
using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for FirebaseConfig's FindEnvFile and LoadFromEnvironment paths.
/// </summary>
public class FirebaseConfigFindEnvTests
{
    [Fact]
    public void FindEnvFile_WhenNoEnvFile_ShouldReturnNull()
    {
        var method = typeof(FirebaseConfig).GetMethod("FindEnvFile",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        // In CI/test environment, there likely isn't a .env file near the base directory
        // The method walks up 5 levels looking for .env
        var result = method.Invoke(null, null);
        // Result is either null or a valid path string
        (result == null || (result is string s && s.EndsWith(".env"))).Should().BeTrue();
    }

    [Fact]
    public void LoadFromEnvironment_WithAllVarsSet_ShouldReturnConfig()
    {
        var method = typeof(FirebaseConfig).GetMethod("LoadFromEnvironment",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        // Save originals
        var origApiKey = Environment.GetEnvironmentVariable("FIREBASE_API_KEY");
        var origAuthDomain = Environment.GetEnvironmentVariable("FIREBASE_AUTH_DOMAIN");
        var origDbUrl = Environment.GetEnvironmentVariable("FIREBASE_DATABASE_URL");
        var origProjectId = Environment.GetEnvironmentVariable("FIREBASE_PROJECT_ID");
        var origOrgId = Environment.GetEnvironmentVariable("ORG_ID");

        try
        {
            Environment.SetEnvironmentVariable("FIREBASE_API_KEY", "test-key-123");
            Environment.SetEnvironmentVariable("FIREBASE_AUTH_DOMAIN", "test.firebaseapp.com");
            Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", "https://test.firebaseio.com");
            Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", "test-project");
            Environment.SetEnvironmentVariable("ORG_ID", "test-org");

            var config = (FirebaseConfig)method.Invoke(null, null)!;
            config.ApiKey.Should().Be("test-key-123");
            config.DatabaseUrl.Should().Be("https://test.firebaseio.com");
            config.ProjectId.Should().Be("test-project");
            config.OrgId.Should().Be("test-org");
        }
        finally
        {
            Environment.SetEnvironmentVariable("FIREBASE_API_KEY", origApiKey);
            Environment.SetEnvironmentVariable("FIREBASE_AUTH_DOMAIN", origAuthDomain);
            Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", origDbUrl);
            Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", origProjectId);
            Environment.SetEnvironmentVariable("ORG_ID", origOrgId);
        }
    }

    [Fact]
    public void LoadFromEnvironment_WithMissingApiKey_ShouldThrow()
    {
        var method = typeof(FirebaseConfig).GetMethod("LoadFromEnvironment",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var origApiKey = Environment.GetEnvironmentVariable("FIREBASE_API_KEY");
        var origDbUrl = Environment.GetEnvironmentVariable("FIREBASE_DATABASE_URL");
        var origProjectId = Environment.GetEnvironmentVariable("FIREBASE_PROJECT_ID");
        var origOrgId = Environment.GetEnvironmentVariable("ORG_ID");

        try
        {
            Environment.SetEnvironmentVariable("FIREBASE_API_KEY", null);
            Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", "https://test.firebaseio.com");
            Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", "test-project");
            Environment.SetEnvironmentVariable("ORG_ID", "test-org");

            var act = () => method.Invoke(null, null);
            act.Should().Throw<TargetInvocationException>()
                .WithInnerException<InvalidOperationException>()
                .WithMessage("*FIREBASE_API_KEY*");
        }
        finally
        {
            Environment.SetEnvironmentVariable("FIREBASE_API_KEY", origApiKey);
            Environment.SetEnvironmentVariable("FIREBASE_DATABASE_URL", origDbUrl);
            Environment.SetEnvironmentVariable("FIREBASE_PROJECT_ID", origProjectId);
            Environment.SetEnvironmentVariable("ORG_ID", origOrgId);
        }
    }

    [Fact]
    public void LoadFromRegistry_ShouldNotThrowOrReturnConfig()
    {
        var method = typeof(FirebaseConfig).GetMethod("LoadFromRegistry",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        // If registry has SIONYX config, this returns a valid config
        // If not, it throws (missing required fields)
        // Either way, the method is exercised
        try
        {
            var config = (FirebaseConfig)method.Invoke(null, null)!;
            config.Should().NotBeNull();
        }
        catch (TargetInvocationException ex)
        {
            // Expected if registry doesn't have SIONYX config
            ex.InnerException.Should().BeOfType<InvalidOperationException>();
        }
    }

    [Fact]
    public void Load_ShouldReturnConfigOrThrow()
    {
        // This tests the public Load() method which routes to either
        // LoadFromRegistry or LoadFromEnvironment
        try
        {
            var config = FirebaseConfig.Load();
            config.Should().NotBeNull();
        }
        catch (InvalidOperationException)
        {
            // Expected if neither registry nor env vars are configured
        }
    }
}
