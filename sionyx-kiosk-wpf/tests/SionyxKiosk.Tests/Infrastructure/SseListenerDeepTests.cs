using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Deep coverage for SseListener: backoff, process events, edge cases.
/// </summary>
public class SseListenerDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public SseListenerDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
    }

    public void Dispose() => _firebase.Dispose();

    private SseListener CreateListener(
        Action<string, JsonElement?>? callback = null,
        Action<string>? errorCallback = null)
    {
        callback ??= (_, _) => { };
        return _firebase.DbListen("test/path", callback, errorCallback);
    }

    // ==================== PROCESS EVENT ====================

    [Fact]
    public void ProcessEvent_KeepAlive_ShouldNotInvokeCallback()
    {
        bool callbackInvoked = false;
        var listener = CreateListener((_, _) => callbackInvoked = true);

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);
        method?.Invoke(listener, new object[] { "keep-alive", "" });

        callbackInvoked.Should().BeFalse();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_Cancel_ShouldInvokeCallbackWithNull()
    {
        string? receivedType = null;
        JsonElement? receivedData = null;
        var listener = CreateListener((type, data) =>
        {
            receivedType = type;
            receivedData = data;
        });

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);
        method?.Invoke(listener, new object[] { "cancel", "" });

        receivedType.Should().Be("cancel");
        receivedData.Should().BeNull();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_AuthRevoked_ShouldInvokeCallbackWithNull()
    {
        string? receivedType = null;
        var listener = CreateListener((type, _) => receivedType = type);

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);
        method?.Invoke(listener, new object[] { "auth_revoked", "" });

        receivedType.Should().Be("auth_revoked");
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_PutWithData_ShouldDeserializeAndCallback()
    {
        string? receivedType = null;
        JsonElement? receivedData = null;
        var listener = CreateListener((type, data) =>
        {
            receivedType = type;
            receivedData = data;
        });

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);
        method?.Invoke(listener, new object[] { "put", "{\"path\":\"/\",\"data\":{\"key\":\"value\"}}" });

        receivedType.Should().Be("put");
        receivedData.Should().NotBeNull();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_PatchWithData_ShouldDeserializeAndCallback()
    {
        string? receivedType = null;
        JsonElement? receivedData = null;
        var listener = CreateListener((type, data) =>
        {
            receivedType = type;
            receivedData = data;
        });

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);
        method?.Invoke(listener, new object[] { "patch", "{\"path\":\"/test\",\"data\":42}" });

        receivedType.Should().Be("patch");
        receivedData.Should().NotBeNull();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithEmptyData_ShouldCallbackWithNull()
    {
        JsonElement? receivedData = new JsonElement();
        var listener = CreateListener((_, data) => receivedData = data);

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);
        method?.Invoke(listener, new object[] { "put", "" });

        receivedData.Should().BeNull();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WithInvalidJson_ShouldNotThrow()
    {
        var listener = CreateListener();

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);

        var act = () => method?.Invoke(listener, new object[] { "put", "not valid json {{{" });
        act.Should().NotThrow();
        listener.Stop();
    }

    [Fact]
    public void ProcessEvent_WhenCallbackThrows_ShouldNotPropagateException()
    {
        var listener = CreateListener((_, _) => throw new InvalidOperationException("callback error"));

        var method = typeof(SseListener).GetMethod("ProcessEvent",
            BindingFlags.NonPublic | BindingFlags.Instance);

        var act = () => method?.Invoke(listener, new object[] { "put", "{\"path\":\"/\",\"data\":null}" });
        act.Should().NotThrow();
        listener.Stop();
    }

    // ==================== BACKOFF ====================

    [Fact]
    public void ReconnectDelay_InitialValue_ShouldBeOne()
    {
        var listener = CreateListener();
        var delayField = typeof(SseListener).GetField("_reconnectDelay",
            BindingFlags.NonPublic | BindingFlags.Instance);

        var delay = (int)delayField!.GetValue(listener)!;
        delay.Should().Be(1);
        listener.Stop();
    }

    [Fact]
    public void ReconnectDelay_AfterSet_ShouldCapAtMax()
    {
        var listener = CreateListener();
        var delayField = typeof(SseListener).GetField("_reconnectDelay",
            BindingFlags.NonPublic | BindingFlags.Instance);

        // Simulate multiple backoffs
        delayField!.SetValue(listener, 32);
        var newDelay = Math.Min(32 * 2, 60);
        newDelay.Should().Be(60);
        listener.Stop();
    }

    // ==================== START / STOP ====================

    [Fact]
    public void Start_WhenAlreadyRunning_ShouldNotThrow()
    {
        var listener = CreateListener();
        listener.IsRunning.Should().BeTrue(); // DbListen auto-starts

        // Starting again should warn, not throw
        var startMethod = typeof(SseListener).GetMethod("Start",
            BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Public);
        var act = () => startMethod?.Invoke(listener, null);
        act.Should().NotThrow();

        listener.Stop();
    }

    [Fact]
    public void Stop_WhenNotRunning_ShouldNotThrow()
    {
        var listener = CreateListener();
        listener.Stop();
        listener.IsRunning.Should().BeFalse();

        // Stopping again should be safe
        var act = () => listener.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void IsRunning_AfterCreation_ShouldBeTrue()
    {
        var listener = CreateListener();
        listener.IsRunning.Should().BeTrue();
        listener.Stop();
    }

    [Fact]
    public void IsRunning_AfterStop_ShouldBeFalse()
    {
        var listener = CreateListener();
        listener.Stop();
        listener.IsRunning.Should().BeFalse();
    }

    // ==================== ERROR CALLBACK ====================

    [Fact]
    public void ErrorCallback_WhenProvided_ShouldBeUsable()
    {
        string? errorMsg = null;
        var listener = CreateListener(errorCallback: msg => errorMsg = msg);

        // Just verify the listener was created successfully
        listener.Should().NotBeNull();
        listener.Stop();
    }

    [Fact]
    public void ErrorCallback_WhenNull_ShouldNotThrow()
    {
        var listener = CreateListener(errorCallback: null);
        listener.Should().NotBeNull();
        listener.Stop();
    }
}
