using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for SseListener covering ProcessEvent, Start/Stop, and IsRunning.
/// </summary>
public class SseListenerTests : IDisposable
{
    private readonly FirebaseClient _client;
    private readonly MockHttpHandler _handler;

    public SseListenerTests()
    {
        (_client, _handler) = TestFirebaseFactory.Create();
    }

    public void Dispose() => _client.Dispose();

    [Fact]
    public void Start_ShouldSetIsRunningTrue()
    {
        var listener = _client.DbListen("test/path", (_, _) => { });
        listener.IsRunning.Should().BeTrue();
        listener.Stop();
    }

    [Fact]
    public void Stop_ShouldSetIsRunningFalse()
    {
        var listener = _client.DbListen("test/path", (_, _) => { });
        listener.Stop();
        listener.IsRunning.Should().BeFalse();
    }

    [Fact]
    public void Stop_WhenNotRunning_ShouldNotThrow()
    {
        var listener = _client.DbListen("test/path", (_, _) => { });
        listener.Stop();
        // Stop again should be safe
        var act = () => listener.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void ProcessEvent_WithPutAndJsonData_ShouldInvokeCallback()
    {
        string? receivedEvent = null;
        JsonElement? receivedData = null;

        var listener = _client.DbListen("test/path", (evt, data) =>
        {
            receivedEvent = evt;
            receivedData = data;
        });

        // Invoke ProcessEvent via reflection
        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var jsonStr = JsonSerializer.Serialize(new { path = "/", data = new { foo = "bar" } });
        method.Invoke(listener, new object[] { "put", jsonStr });

        receivedEvent.Should().Be("put");
        receivedData.Should().NotBeNull();

        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithKeepAlive_ShouldNotInvokeCallback()
    {
        var invoked = false;
        var listener = _client.DbListen("test/path", (_, _) => invoked = true);

        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(listener, new object[] { "keep-alive", "" });

        invoked.Should().BeFalse();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithCancel_ShouldInvokeCallbackWithNull()
    {
        string? receivedEvent = null;
        JsonElement? receivedData = null;

        var listener = _client.DbListen("test/path", (evt, data) =>
        {
            receivedEvent = evt;
            receivedData = data;
        });

        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(listener, new object[] { "cancel", "" });

        receivedEvent.Should().Be("cancel");
        receivedData.Should().BeNull();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithAuthRevoked_ShouldInvokeCallbackWithNull()
    {
        string? receivedEvent = null;
        var listener = _client.DbListen("test/path", (evt, _) => receivedEvent = evt);

        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(listener, new object[] { "auth_revoked", "" });

        receivedEvent.Should().Be("auth_revoked");
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithInvalidJson_ShouldNotThrow()
    {
        var listener = _client.DbListen("test/path", (_, _) => { });

        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(listener, new object[] { "put", "not valid json{{{" });
        act.Should().NotThrow();

        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithEmptyData_ShouldInvokeCallbackWithNull()
    {
        JsonElement? receivedData = null;
        var listener = _client.DbListen("test/path", (_, data) => receivedData = data);

        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(listener, new object[] { "put", "" });

        receivedData.Should().BeNull();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithPatch_ShouldInvokeCallback()
    {
        string? receivedEvent = null;
        var listener = _client.DbListen("test/path", (evt, _) => receivedEvent = evt);

        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(listener, new object[] { "patch", "{\"foo\":\"bar\"}" });

        receivedEvent.Should().Be("patch");
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WhenCallbackThrows_ShouldNotCrash()
    {
        var listener = _client.DbListen("test/path", (_, _) => throw new Exception("Boom"));

        var method = typeof(SseListener).GetMethod("ProcessEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(listener, new object[] { "put", "{\"test\":true}" });
        act.Should().NotThrow();

        listener.Stop();
    }

    [Fact]
    public void MultipleStartCalls_ShouldNotCreateDuplicateListeners()
    {
        var callbackCount = 0;
        var callback = new Action<string, JsonElement?>((_, _) => callbackCount++);

        var listener = _client.DbListen("test/path", callback);
        // The listener is already started by DbListen

        // Calling Start again via reflection should be safe (it checks IsRunning)
        var startMethod = typeof(SseListener).GetMethod("Start", BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Public)!;
        startMethod.Invoke(listener, null);

        listener.IsRunning.Should().BeTrue();
        listener.Stop();
    }
}
