using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class FirebaseConfigTests
{
    [Fact]
    public void CreateAndValidate_WithValidData_ShouldSucceed()
    {
        var config = TestFirebaseFactory.CreateConfig();

        config.ApiKey.Should().Be("test-api-key");
        config.AuthDomain.Should().Be("test.firebaseapp.com");
        config.DatabaseUrl.Should().Be("https://test-db.firebaseio.com");
        config.ProjectId.Should().Be("test-project");
        config.OrgId.Should().Be("test-org");
    }

    [Fact]
    public void AuthUrl_ShouldReturnGoogleIdentityUrl()
    {
        var config = TestFirebaseFactory.CreateConfig();
        config.AuthUrl.Should().Contain("identitytoolkit.googleapis.com");
    }

    [Fact]
    public void Load_WithMissingApiKey_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("", "domain", "https://db.example.com", "project", "org");
        act.Should().Throw<InvalidOperationException>().WithMessage("*API_KEY*");
    }

    [Fact]
    public void Load_WithMissingDatabaseUrl_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", "domain", "", "project", "org");
        act.Should().Throw<InvalidOperationException>().WithMessage("*DATABASE_URL*");
    }

    [Fact]
    public void Load_WithMissingProjectId_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", "domain", "https://db.example.com", "", "org");
        act.Should().Throw<InvalidOperationException>().WithMessage("*PROJECT_ID*");
    }

    [Fact]
    public void Load_WithMissingOrgId_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", "domain", "https://db.example.com", "project", "");
        act.Should().Throw<InvalidOperationException>().WithMessage("*ORG_ID*");
    }

    [Fact]
    public void Load_WithInvalidOrgId_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", "domain", "https://db.example.com", "project", "Invalid_Org!");
        act.Should().Throw<InvalidOperationException>().WithMessage("*Invalid ORG_ID*");
    }

    [Fact]
    public void Load_WithValidOrgId_Lowercase_ShouldSucceed()
    {
        var act = () => InvokeCreateAndValidate("key", "domain", "https://db.example.com", "project", "my-org-123");
        act.Should().NotThrow();
    }

    /// <summary>Invoke the private static CreateAndValidate method.</summary>
    private static void InvokeCreateAndValidate(string apiKey, string? authDomain, string databaseUrl, string projectId, string orgId)
    {
        var method = typeof(FirebaseConfig).GetMethod("CreateAndValidate",
            BindingFlags.NonPublic | BindingFlags.Static);

        try
        {
            method!.Invoke(null, new object?[] { apiKey, authDomain, databaseUrl, projectId, orgId, "test" });
        }
        catch (TargetInvocationException ex) when (ex.InnerException != null)
        {
            throw ex.InnerException;
        }
    }
}
