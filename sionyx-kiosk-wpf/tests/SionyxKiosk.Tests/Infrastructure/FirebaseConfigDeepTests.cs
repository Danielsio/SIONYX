using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Deep tests for FirebaseConfig covering CreateAndValidate with various inputs.
/// </summary>
public class FirebaseConfigDeepTests
{
    private static readonly MethodInfo CreateAndValidateMethod = typeof(FirebaseConfig).GetMethod(
        "CreateAndValidate", BindingFlags.NonPublic | BindingFlags.Static)!;

    private static FirebaseConfig InvokeCreateAndValidate(
        string? apiKey, string? authDomain, string? databaseUrl,
        string? projectId, string? orgId, string source = "test")
    {
        return (FirebaseConfig)CreateAndValidateMethod.Invoke(null,
            new object?[] { apiKey, authDomain, databaseUrl, projectId, orgId, source })!;
    }

    [Fact]
    public void CreateAndValidate_WithValidInputs_ShouldReturnConfig()
    {
        var config = InvokeCreateAndValidate("key", "auth.domain", "https://db.firebaseio.com", "proj", "my-org");
        config.Should().NotBeNull();
        config.ApiKey.Should().Be("key");
        config.DatabaseUrl.Should().Be("https://db.firebaseio.com");
        config.ProjectId.Should().Be("proj");
        config.OrgId.Should().Be("my-org");
        config.AuthDomain.Should().Be("auth.domain");
    }

    [Fact]
    public void CreateAndValidate_WithNullAuthDomain_ShouldStillWork()
    {
        var config = InvokeCreateAndValidate("key", null, "https://db.firebaseio.com", "proj", "my-org");
        config.AuthDomain.Should().BeNull();
    }

    [Fact]
    public void AuthUrl_ShouldReturnStandardFirebaseUrl()
    {
        var config = TestFirebaseFactory.CreateConfig();
        config.AuthUrl.Should().Contain("identitytoolkit.googleapis.com");
    }

    [Fact]
    public void CreateAndValidate_WithMissingApiKey_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate(null, null, "https://db.firebaseio.com", "proj", "org");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*FIREBASE_API_KEY*");
    }

    [Fact]
    public void CreateAndValidate_WithEmptyApiKey_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("", null, "https://db.firebaseio.com", "proj", "org");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*FIREBASE_API_KEY*");
    }

    [Fact]
    public void CreateAndValidate_WithMissingDatabaseUrl_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", null, null, "proj", "org");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*FIREBASE_DATABASE_URL*");
    }

    [Fact]
    public void CreateAndValidate_WithMissingProjectId_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", null, "https://db.firebaseio.com", null, "org");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*FIREBASE_PROJECT_ID*");
    }

    [Fact]
    public void CreateAndValidate_WithMissingOrgId_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", null, "https://db.firebaseio.com", "proj", null);
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*ORG_ID*");
    }

    [Fact]
    public void CreateAndValidate_WithInvalidOrgId_Uppercase_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", null, "https://db.firebaseio.com", "proj", "MyOrg");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*Invalid ORG_ID*");
    }

    [Fact]
    public void CreateAndValidate_WithInvalidOrgId_Spaces_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", null, "https://db.firebaseio.com", "proj", "my org");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*Invalid ORG_ID*");
    }

    [Fact]
    public void CreateAndValidate_WithInvalidOrgId_SpecialChars_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("key", null, "https://db.firebaseio.com", "proj", "my@org!");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>()
            .WithMessage("*Invalid ORG_ID*");
    }

    [Theory]
    [InlineData("my-org")]
    [InlineData("tech-lab")]
    [InlineData("university-cs")]
    [InlineData("abc123")]
    [InlineData("a-b-c-1-2-3")]
    public void CreateAndValidate_WithValidOrgIds_ShouldSucceed(string orgId)
    {
        var config = InvokeCreateAndValidate("key", null, "https://db.firebaseio.com", "proj", orgId);
        config.OrgId.Should().Be(orgId);
    }

    [Fact]
    public void CreateAndValidate_WithWhitespaceOnlyApiKey_ShouldThrow()
    {
        var act = () => InvokeCreateAndValidate("   ", null, "https://db.firebaseio.com", "proj", "org");
        act.Should().Throw<TargetInvocationException>()
            .WithInnerException<InvalidOperationException>();
    }

    [Fact]
    public void FindEnvFile_ShouldNotThrow()
    {
        var method = typeof(FirebaseConfig).GetMethod("FindEnvFile", BindingFlags.NonPublic | BindingFlags.Static)!;
        var act = () => method.Invoke(null, null);
        act.Should().NotThrow();
    }
}
