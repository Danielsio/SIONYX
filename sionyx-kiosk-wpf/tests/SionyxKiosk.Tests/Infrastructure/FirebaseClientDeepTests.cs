using System.Net;
using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Deep tests for FirebaseClient covering EnsureValidTokenAsync paths,
/// ParseFirebaseError, ClearAuth, RestoreAuth, and all DB operations.
/// </summary>
public class FirebaseClientDeepTests : IDisposable
{
    private readonly FirebaseClient _client;
    private readonly MockHttpHandler _handler;

    public FirebaseClientDeepTests()
    {
        (_client, _handler) = TestFirebaseFactory.Create();
    }

    public void Dispose() => _client.Dispose();

    // ==================== EnsureValidTokenAsync ====================

    [Fact]
    public async Task EnsureValidTokenAsync_WhenNotAuthenticated_ShouldReturnFalse()
    {
        var (client, _) = TestFirebaseFactory.CreateUnauthenticated();
        var result = await client.EnsureValidTokenAsync();
        result.Should().BeFalse();
        client.Dispose();
    }

    [Fact]
    public async Task EnsureValidTokenAsync_WhenTokenValid_ShouldReturnTrue()
    {
        // Token was set via RestoreAuth with 30min expiry, so it's valid
        var result = await _client.EnsureValidTokenAsync();
        result.Should().BeTrue();
    }

    [Fact]
    public async Task EnsureValidTokenAsync_WhenTokenExpired_ShouldRefresh()
    {
        // Set token expiry to past via reflection
        var expiryField = typeof(FirebaseClient).GetField("_tokenExpiry", BindingFlags.NonPublic | BindingFlags.Instance)!;
        expiryField.SetValue(_client, DateTime.UtcNow.AddMinutes(-10));

        // Mock the refresh token endpoint
        _handler.When("securetoken.googleapis.com", new
        {
            id_token = "new-id-token",
            refresh_token = "new-refresh-token",
            user_id = "test-uid",
            expires_in = "3600",
        });

        var result = await _client.EnsureValidTokenAsync();
        result.Should().BeTrue();
    }

    [Fact]
    public async Task EnsureValidTokenAsync_WhenRefreshFails_ShouldReturnFalse()
    {
        // Set token expiry to past
        var expiryField = typeof(FirebaseClient).GetField("_tokenExpiry", BindingFlags.NonPublic | BindingFlags.Instance)!;
        expiryField.SetValue(_client, DateTime.UtcNow.AddMinutes(-10));

        // Mock refresh failure
        _handler.WhenError("securetoken.googleapis.com", HttpStatusCode.Unauthorized);

        var result = await _client.EnsureValidTokenAsync();
        result.Should().BeFalse();
    }

    // ==================== ClearAuth / RestoreAuth ====================

    [Fact]
    public void ClearAuth_ShouldClearAllAuthState()
    {
        _client.IsAuthenticated.Should().BeTrue();
        _client.ClearAuth();
        _client.IsAuthenticated.Should().BeFalse();
        _client.UserId.Should().BeNull();
        _client.RefreshToken.Should().BeNull();
    }

    [Fact]
    public void RestoreAuth_ShouldRestoreAuthState()
    {
        var (client, _) = TestFirebaseFactory.CreateUnauthenticated();
        client.IsAuthenticated.Should().BeFalse();

        client.RestoreAuth("id-tok", "refresh-tok", "user-123");

        client.IsAuthenticated.Should().BeTrue();
        client.UserId.Should().Be("user-123");
        client.RefreshToken.Should().Be("refresh-tok");
        client.Dispose();
    }

    // ==================== RefreshTokenAsync ====================

    [Fact]
    public async Task RefreshTokenAsync_WithNoRefreshToken_ShouldReturnFalse()
    {
        var (client, _) = TestFirebaseFactory.CreateUnauthenticated();
        var result = await client.RefreshTokenAsync();
        result.Should().BeFalse();
        client.Dispose();
    }

    [Fact]
    public async Task RefreshTokenAsync_WithValidToken_ShouldUpdateTokens()
    {
        _handler.When("securetoken.googleapis.com", new
        {
            id_token = "refreshed-id-token",
            refresh_token = "refreshed-refresh-token",
            user_id = "test-uid",
            expires_in = "7200",
        });

        var result = await _client.RefreshTokenAsync();
        result.Should().BeTrue();
        _client.RefreshToken.Should().Be("refreshed-refresh-token");
    }

    [Fact]
    public async Task RefreshTokenAsync_WhenFails_ShouldReturnFalse()
    {
        _handler.WhenError("securetoken.googleapis.com", HttpStatusCode.Unauthorized);
        var result = await _client.RefreshTokenAsync();
        result.Should().BeFalse();
    }

    // ==================== DB Operations Error Paths ====================

    [Fact]
    public async Task DbGetAsync_WhenNotAuthenticated_ShouldFail()
    {
        var (client, handler) = TestFirebaseFactory.CreateUnauthenticated();
        var result = await client.DbGetAsync("test/path");
        result.Success.Should().BeFalse();
        result.Error.Should().Contain("Not authenticated");
        client.Dispose();
    }

    [Fact]
    public async Task DbSetAsync_WhenNotAuthenticated_ShouldFail()
    {
        var (client, _) = TestFirebaseFactory.CreateUnauthenticated();
        var result = await client.DbSetAsync("test/path", new { foo = "bar" });
        result.Success.Should().BeFalse();
        client.Dispose();
    }

    [Fact]
    public async Task DbUpdateAsync_WhenNotAuthenticated_ShouldFail()
    {
        var (client, _) = TestFirebaseFactory.CreateUnauthenticated();
        var result = await client.DbUpdateAsync("test/path", new { foo = "bar" });
        result.Success.Should().BeFalse();
        client.Dispose();
    }

    [Fact]
    public async Task DbDeleteAsync_WhenNotAuthenticated_ShouldFail()
    {
        var (client, _) = TestFirebaseFactory.CreateUnauthenticated();
        var result = await client.DbDeleteAsync("test/path");
        result.Success.Should().BeFalse();
        client.Dispose();
    }

    [Fact]
    public async Task DbGetAsync_WhenServerError_ShouldFail()
    {
        _handler.WhenError("test-db.firebaseio.com");
        var result = await _client.DbGetAsync("test/path");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbSetAsync_WhenServerError_ShouldFail()
    {
        _handler.WhenError("test-db.firebaseio.com");
        var result = await _client.DbSetAsync("test/path", new { foo = "bar" });
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbUpdateAsync_WhenServerError_ShouldFail()
    {
        _handler.WhenError("test-db.firebaseio.com");
        var result = await _client.DbUpdateAsync("test/path", new { foo = "bar" });
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbDeleteAsync_WhenServerError_ShouldFail()
    {
        _handler.WhenError("test-db.firebaseio.com");
        var result = await _client.DbDeleteAsync("test/path");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbGetAsync_WithValidResponse_ShouldReturnData()
    {
        _handler.When("test-db.firebaseio.com", new { name = "Test", value = 42 });
        var result = await _client.DbGetAsync("mypath");
        result.Success.Should().BeTrue();
        result.Data.Should().NotBeNull();
    }

    [Fact]
    public async Task DbSetAsync_WithValidData_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var result = await _client.DbSetAsync("mypath", new { name = "Test" });
        result.Success.Should().BeTrue();
    }

    [Fact]
    public async Task DbUpdateAsync_WithValidData_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var result = await _client.DbUpdateAsync("mypath", new { name = "Updated" });
        result.Success.Should().BeTrue();
    }

    [Fact]
    public async Task DbDeleteAsync_WithValidPath_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var result = await _client.DbDeleteAsync("mypath");
        result.Success.Should().BeTrue();
    }

    // ==================== DbListen (SSE) ====================

    [Fact]
    public void DbListen_ShouldReturnSseListener()
    {
        var listener = _client.DbListen("test/path", (_, _) => { });
        listener.Should().NotBeNull();
        listener.IsRunning.Should().BeTrue();
        listener.Stop();
    }

    [Fact]
    public void DbListen_WithErrorCallback_ShouldReturnSseListener()
    {
        var listener = _client.DbListen("test/path", (_, _) => { }, err => { });
        listener.Should().NotBeNull();
        listener.Stop();
    }

    // ==================== SignIn / SignUp Error Translation ====================

    [Fact]
    public async Task SignInAsync_WithEmailExists_ShouldReturnTranslatedError()
    {
        _handler.WhenFirebaseError("signInWithPassword", "EMAIL_EXISTS");

        var result = await _client.SignInAsync("test@test.com", "pass");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task SignUpAsync_WithWeakPassword_ShouldReturnTranslatedError()
    {
        _handler.WhenFirebaseError("signUp", "WEAK_PASSWORD");

        var result = await _client.SignUpAsync("test@test.com", "123");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task SignInAsync_WithTooManyAttempts_ShouldReturnTranslatedError()
    {
        _handler.WhenFirebaseError("signInWithPassword", "TOO_MANY_ATTEMPTS_TRY_LATER");

        var result = await _client.SignInAsync("test@test.com", "pass");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task SignInAsync_WithUserDisabled_ShouldReturnTranslatedError()
    {
        _handler.WhenFirebaseError("signInWithPassword", "USER_DISABLED");

        var result = await _client.SignInAsync("test@test.com", "pass");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task SignInAsync_WithInvalidEmail_ShouldReturnTranslatedError()
    {
        _handler.WhenFirebaseError("signInWithPassword", "INVALID_EMAIL");

        var result = await _client.SignInAsync("bad", "pass");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task SignInAsync_WithMissingPassword_ShouldReturnTranslatedError()
    {
        _handler.WhenFirebaseError("signInWithPassword", "MISSING_PASSWORD");

        var result = await _client.SignInAsync("test@test.com", "");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task SignInAsync_WithInvalidLoginCredentials_ShouldReturnTranslatedError()
    {
        _handler.WhenFirebaseError("signInWithPassword", "INVALID_LOGIN_CREDENTIALS");

        var result = await _client.SignInAsync("test@test.com", "wrong");
        result.Success.Should().BeFalse();
    }

    // ==================== Internal Properties ====================

    [Fact]
    public void OrgId_ShouldReturnConfiguredValue()
    {
        _client.OrgId.Should().Be("test-org");
    }

    [Fact]
    public void DatabaseUrl_Internal_ShouldReturnConfiguredValue()
    {
        // Access via internal property
        var dbUrl = typeof(FirebaseClient)
            .GetProperty("DatabaseUrl", BindingFlags.NonPublic | BindingFlags.Instance)?
            .GetValue(_client) as string;
        dbUrl.Should().Be("https://test-db.firebaseio.com");
    }

    [Fact]
    public void GetOrgPathInternal_ShouldPrependOrgPrefix()
    {
        var method = typeof(FirebaseClient).GetMethod("GetOrgPathInternal", BindingFlags.NonPublic | BindingFlags.Instance);
        var result = method?.Invoke(_client, new object[] { "users/test" }) as string;
        result.Should().Be("organizations/test-org/users/test");
    }

}
