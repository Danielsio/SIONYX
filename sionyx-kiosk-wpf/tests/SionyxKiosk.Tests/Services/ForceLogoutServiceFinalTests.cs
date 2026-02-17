using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Final coverage tests for ForceLogoutService: first-event skip logic,
/// stale data handling, exception resilience.
/// </summary>
public class ForceLogoutServiceFinalTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ForceLogoutService _service;

    public ForceLogoutServiceFinalTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _handler.SetDefaultSuccess();
        _service = new ForceLogoutService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    private void InvokeOnEvent(string eventType, JsonElement? data)
    {
        var method = typeof(ForceLogoutService).GetMethod("OnEvent",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, new object?[] { eventType, data });
    }

    private void SetFirstEvent(bool value)
    {
        var field = typeof(ForceLogoutService).GetField("_isFirstEvent",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        field.SetValue(_service, value);
    }

    // ==================== FIRST EVENT SKIP ====================

    [Fact]
    public void OnEvent_FirstEvent_WithNullData_ShouldSkipAndNotFire()
    {
        SetFirstEvent(true);

        bool fired = false;
        _service.ForceLogout += _ => fired = true;

        var nullElement = JsonSerializer.Deserialize<JsonElement>("null");
        InvokeOnEvent("put", nullElement);

        fired.Should().BeFalse();
    }

    [Fact]
    public void OnEvent_FirstEvent_WithStaleData_ShouldSkipAndClearFlag()
    {
        SetFirstEvent(true);

        // Set _userId so the delete path works
        var userIdField = typeof(ForceLogoutService).GetField("_userId",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        userIdField.SetValue(_service, "test-user");

        bool fired = false;
        _service.ForceLogout += _ => fired = true;

        var staleData = TestFirebaseFactory.ToJsonElement(new { reason = "old_logout" });
        InvokeOnEvent("put", staleData);

        fired.Should().BeFalse(); // First event is always skipped
    }

    [Fact]
    public void OnEvent_SecondEvent_AfterFirst_ShouldFireNormally()
    {
        SetFirstEvent(true);

        string? reason = null;
        _service.ForceLogout += r => reason = r;

        // First event: skipped
        var nullElement = JsonSerializer.Deserialize<JsonElement>("null");
        InvokeOnEvent("put", nullElement);
        reason.Should().BeNull();

        // Second event: should fire
        var data = TestFirebaseFactory.ToJsonElement(new { reason = "admin_kicked" });
        InvokeOnEvent("put", data);
        reason.Should().Be("admin_kicked");
    }

    // ==================== KEEP-ALIVE / PATCH EVENTS ====================

    [Fact]
    public void OnEvent_KeepAlive_ShouldNotFire()
    {
        bool fired = false;
        _service.ForceLogout += _ => fired = true;

        InvokeOnEvent("keep-alive", null);
        fired.Should().BeFalse();
    }

    [Fact]
    public void OnEvent_Cancel_ShouldNotFire()
    {
        bool fired = false;
        _service.ForceLogout += _ => fired = true;

        InvokeOnEvent("cancel", null);
        fired.Should().BeFalse();
    }

    // ==================== JSON NULL SECOND EVENT ====================

    [Fact]
    public void OnEvent_SecondEvent_JsonNull_ShouldNotFire()
    {
        // Reset first event flag
        SetFirstEvent(false);

        bool fired = false;
        _service.ForceLogout += _ => fired = true;

        var nullElement = JsonSerializer.Deserialize<JsonElement>("null");
        InvokeOnEvent("put", nullElement);

        fired.Should().BeFalse();
    }

    // ==================== START/STOP LIFECYCLE ====================

    [Fact]
    public void StartListening_ShouldBeReentrant()
    {
        _service.StartListening("user-1");
        _service.StartListening("user-1");
        _service.StopListening();
    }

    [Fact]
    public void StopListening_CalledMultipleTimes_ShouldNotThrow()
    {
        _service.StartListening("user-1");
        _service.StopListening();
        _service.StopListening();
        _service.StopListening();
    }
}
