using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for ForceLogoutService covering OnEvent processing.
/// </summary>
public class ForceLogoutServiceDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ForceLogoutService _service;

    public ForceLogoutServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ForceLogoutService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void OnEvent_WithPutAndReason_ShouldRaiseForceLogout()
    {
        string? receivedReason = null;
        _service.ForceLogout += r => receivedReason = r;

        var method = typeof(ForceLogoutService).GetMethod("OnEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var data = TestFirebaseFactory.ToJsonElement(new { reason = "admin_kicked" });
        method.Invoke(_service, new object?[] { "put", (JsonElement?)data });

        receivedReason.Should().Be("admin_kicked");
    }

    [Fact]
    public void OnEvent_WithPutAndNoReason_ShouldUseDefaultReason()
    {
        string? receivedReason = null;
        _service.ForceLogout += r => receivedReason = r;

        var method = typeof(ForceLogoutService).GetMethod("OnEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var data = TestFirebaseFactory.ToJsonElement(new { timestamp = DateTime.Now.ToString("o") });
        method.Invoke(_service, new object?[] { "put", (JsonElement?)data });

        receivedReason.Should().Be("admin_forced");
    }

    [Fact]
    public void OnEvent_WithNullData_ShouldNotRaiseEvent()
    {
        var raised = false;
        _service.ForceLogout += _ => raised = true;

        var method = typeof(ForceLogoutService).GetMethod("OnEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, new object?[] { "put", null });

        raised.Should().BeFalse();
    }

    [Fact]
    public void OnEvent_WithNonPutEvent_ShouldNotRaiseEvent()
    {
        var raised = false;
        _service.ForceLogout += _ => raised = true;

        var method = typeof(ForceLogoutService).GetMethod("OnEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var data = TestFirebaseFactory.ToJsonElement(new { reason = "test" });
        method.Invoke(_service, new object?[] { "patch", (JsonElement?)data });

        raised.Should().BeFalse();
    }

    [Fact]
    public void OnEvent_WithJsonNull_ShouldNotRaiseEvent()
    {
        var raised = false;
        _service.ForceLogout += _ => raised = true;

        var method = typeof(ForceLogoutService).GetMethod("OnEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var nullElement = JsonSerializer.Deserialize<JsonElement>("null");
        method.Invoke(_service, new object?[] { "put", (JsonElement?)nullElement });

        raised.Should().BeFalse();
    }

    [Fact]
    public void StartListening_ShouldStartWithoutError()
    {
        var act = () => _service.StartListening("test-user-id");
        act.Should().NotThrow();
        _service.StopListening();
    }

    [Fact]
    public void StopListening_WhenNotStarted_ShouldNotThrow()
    {
        var act = () => _service.StopListening();
        act.Should().NotThrow();
    }

    [Fact]
    public void StartListening_ThenStartAgain_ShouldReplace()
    {
        _service.StartListening("user-1");
        var act = () => _service.StartListening("user-2");
        act.Should().NotThrow();
        _service.StopListening();
    }
}
