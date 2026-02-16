using System.Net;
using System.Text;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class FirebaseClientTests : IDisposable
{
    private readonly FirebaseClient _client;
    private readonly MockHttpHandler _handler;

    public FirebaseClientTests()
    {
        (_client, _handler) = TestFirebaseFactory.Create();
    }

    public void Dispose() => _client.Dispose();

    // ==================== AUTH STATE ====================

    [Fact]
    public void IsAuthenticated_WhenTokenSet_ShouldReturnTrue()
    {
        _client.IsAuthenticated.Should().BeTrue();
    }

    [Fact]
    public void IsAuthenticated_WhenCleared_ShouldReturnFalse()
    {
        _client.ClearAuth();
        _client.IsAuthenticated.Should().BeFalse();
    }

    [Fact]
    public void UserId_ShouldReturnSetValue()
    {
        _client.UserId.Should().Be("test-uid");
    }

    [Fact]
    public void RefreshToken_ShouldReturnSetValue()
    {
        _client.RefreshToken.Should().Be("test-refresh-token");
    }

    [Fact]
    public void OrgId_ShouldReturnConfigValue()
    {
        _client.OrgId.Should().Be("test-org");
    }

    [Fact]
    public void ClearAuth_ShouldResetAllAuthState()
    {
        _client.ClearAuth();
        _client.UserId.Should().BeNull();
        _client.RefreshToken.Should().BeNull();
        _client.IsAuthenticated.Should().BeFalse();
    }

    [Fact]
    public void RestoreAuth_ShouldSetAllAuthState()
    {
        _client.ClearAuth();
        _client.RestoreAuth("new-token", "new-refresh", "new-uid");
        _client.UserId.Should().Be("new-uid");
        _client.RefreshToken.Should().Be("new-refresh");
        _client.IsAuthenticated.Should().BeTrue();
    }

    // ==================== DATABASE OPERATIONS ====================

    [Fact]
    public async Task DbGetAsync_WhenAuthenticated_ShouldReturnData()
    {
        _handler.When("users/test-uid.json", new { firstName = "John", lastName = "Doe" });

        var result = await _client.DbGetAsync("users/test-uid");

        result.Success.Should().BeTrue();
        result.Data.Should().NotBeNull();
    }

    [Fact]
    public async Task DbGetAsync_WhenNotAuthenticated_ShouldFail()
    {
        _client.ClearAuth();
        var result = await _client.DbGetAsync("users/test-uid");
        result.Success.Should().BeFalse();
        result.Error.Should().Be("Not authenticated");
    }

    [Fact]
    public async Task DbGetAsync_WhenHttpError_ShouldFail()
    {
        _handler.WhenError("users");
        var result = await _client.DbGetAsync("users/test-uid");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbSetAsync_WhenAuthenticated_ShouldSucceed()
    {
        var result = await _client.DbSetAsync("users/test-uid", new { name = "Test" });
        result.Success.Should().BeTrue();
    }

    [Fact]
    public async Task DbSetAsync_WhenNotAuthenticated_ShouldFail()
    {
        _client.ClearAuth();
        var result = await _client.DbSetAsync("users/test-uid", new { name = "Test" });
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbUpdateAsync_WhenAuthenticated_ShouldSucceed()
    {
        var result = await _client.DbUpdateAsync("users/test-uid", new { name = "Updated" });
        result.Success.Should().BeTrue();
    }

    [Fact]
    public async Task DbUpdateAsync_WhenNotAuthenticated_ShouldFail()
    {
        _client.ClearAuth();
        var result = await _client.DbUpdateAsync("users/test-uid", new { name = "Updated" });
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbDeleteAsync_WhenAuthenticated_ShouldSucceed()
    {
        var result = await _client.DbDeleteAsync("users/test-uid/forceLogout");
        result.Success.Should().BeTrue();
    }

    [Fact]
    public async Task DbDeleteAsync_WhenNotAuthenticated_ShouldFail()
    {
        _client.ClearAuth();
        var result = await _client.DbDeleteAsync("users/test-uid/forceLogout");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task DbGetAsync_ShouldUseOrgPath()
    {
        await _client.DbGetAsync("users/123");
        _handler.SentRequests.Should().ContainSingle(r =>
            r.RequestUri!.ToString().Contains("organizations/test-org/users/123"));
    }

    [Fact]
    public async Task DbSetAsync_ShouldUsePutMethod()
    {
        await _client.DbSetAsync("test/path", new { data = true });
        _handler.SentRequests.Should().ContainSingle(r =>
            r.Method == HttpMethod.Put);
    }

    [Fact]
    public async Task DbUpdateAsync_ShouldUsePatchMethod()
    {
        await _client.DbUpdateAsync("test/path", new { data = true });
        _handler.SentRequests.Should().ContainSingle(r =>
            r.Method == HttpMethod.Patch);
    }

    [Fact]
    public async Task DbDeleteAsync_ShouldUseDeleteMethod()
    {
        await _client.DbDeleteAsync("test/path");
        _handler.SentRequests.Should().ContainSingle(r =>
            r.Method == HttpMethod.Delete);
    }

    // ==================== SIGN IN / SIGN UP ====================

    [Fact]
    public async Task SignInAsync_WithValidCredentials_ShouldSucceed()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "new-id-token",
            refreshToken = "new-refresh-token",
            localId = "user-123",
            expiresIn = "3600"
        });

        var result = await _client.SignInAsync("test@example.com", "password123");
        result.Success.Should().BeTrue();
        _client.UserId.Should().Be("user-123");
    }

    [Fact]
    public async Task SignInAsync_WithInvalidCredentials_ShouldFail()
    {
        _handler.WhenError("signInWithPassword", HttpStatusCode.BadRequest);

        var result = await _client.SignInAsync("test@example.com", "wrong");
        result.Success.Should().BeFalse();
    }

    [Fact]
    public async Task SignUpAsync_WithValidData_ShouldSucceed()
    {
        _handler.When("signUp", new
        {
            idToken = "new-id-token",
            refreshToken = "new-refresh-token",
            localId = "user-456",
            expiresIn = "3600"
        });

        var result = await _client.SignUpAsync("new@example.com", "password123");
        result.Success.Should().BeTrue();
        _client.UserId.Should().Be("user-456");
    }

    [Fact]
    public async Task SignUpAsync_WithError_ShouldFail()
    {
        _handler.WhenError("signUp", HttpStatusCode.BadRequest);

        var result = await _client.SignUpAsync("existing@example.com", "password");
        result.Success.Should().BeFalse();
    }

    // ==================== TOKEN REFRESH ====================

    [Fact]
    public async Task RefreshTokenAsync_WithNoToken_ShouldReturnFalse()
    {
        _client.ClearAuth();
        var result = await _client.RefreshTokenAsync();
        result.Should().BeFalse();
    }

    [Fact]
    public async Task RefreshTokenAsync_WithToken_ShouldRefresh()
    {
        _handler.When("securetoken.googleapis.com", new
        {
            id_token = "refreshed-token",
            refresh_token = "refreshed-refresh",
            user_id = "test-uid",
            expires_in = "3600"
        });

        var result = await _client.RefreshTokenAsync();
        result.Should().BeTrue();
    }

    [Fact]
    public async Task EnsureValidTokenAsync_WhenNoToken_ShouldReturnFalse()
    {
        _client.ClearAuth();
        var result = await _client.EnsureValidTokenAsync();
        result.Should().BeFalse();
    }

    [Fact]
    public async Task EnsureValidTokenAsync_WhenTokenValid_ShouldReturnTrue()
    {
        var result = await _client.EnsureValidTokenAsync();
        result.Should().BeTrue();
    }

    // ==================== SSE ====================

    [Fact]
    public void DbListen_ShouldReturnSseListener()
    {
        var listener = _client.DbListen("test/path", (_, _) => { });
        listener.Should().NotBeNull();
        listener.Stop(); // Cleanup
    }

}

public class FirebaseResultTests
{
    [Fact]
    public void Ok_WithoutData_ShouldBeSuccessful()
    {
        var result = FirebaseResult.Ok();
        result.Success.Should().BeTrue();
        result.Data.Should().BeNull();
        result.Error.Should().BeNull();
    }

    [Fact]
    public void Ok_WithData_ShouldContainData()
    {
        var data = new { name = "Test" };
        var result = FirebaseResult.Ok(data);
        result.Success.Should().BeTrue();
        result.Data.Should().Be(data);
    }

    [Fact]
    public void Fail_ShouldContainError()
    {
        var result = FirebaseResult.Fail("Something went wrong");
        result.Success.Should().BeFalse();
        result.Error.Should().Be("Something went wrong");
    }
}

public class FirebaseApiExceptionTests
{
    [Fact]
    public void Constructor_ShouldSetProperties()
    {
        var ex = new FirebaseApiException(HttpStatusCode.BadRequest, "{\"error\":{\"message\":\"INVALID_PASSWORD\"}}");
        ex.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        ex.ResponseBody.Should().Contain("INVALID_PASSWORD");
        ex.Message.Should().Contain("BadRequest");
    }

    [Fact]
    public void Constructor_ShouldIncludeResponseInMessage()
    {
        var ex = new FirebaseApiException(HttpStatusCode.Unauthorized, "unauthorized");
        ex.Message.Should().Contain("unauthorized");
    }
}
