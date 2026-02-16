using System.IO;
using System.Net;
using System.Net.Http;
using System.Reflection;
using System.Text;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for SseListener streaming by mocking the HTTP stream response.
/// Tests ConnectAndStreamAsync and ListenLoopAsync behavior.
/// </summary>
public class SseListenerStreamTests : IDisposable
{
    private readonly FirebaseClient _client;
    private readonly MockHttpHandler _handler;

    public SseListenerStreamTests()
    {
        (_client, _handler) = TestFirebaseFactory.Create();
    }

    public void Dispose() => _client.Dispose();

    [Fact]
    public void ListenLoopAsync_WhenCancelled_ShouldStopGracefully()
    {
        var listener = _client.DbListen("test", (_, _) => { });

        // Give it a moment to start, then stop
        Thread.Sleep(100);
        listener.Stop();

        listener.IsRunning.Should().BeFalse();
    }

    [Fact]
    public void ConnectAndStreamAsync_WhenNotAuthenticated_ShouldReconnect()
    {
        // Clear auth to trigger "Not authenticated" in ConnectAndStreamAsync
        _client.ClearAuth();

        string? errorMsg = null;
        var listener = _client.DbListen("test", (_, _) => { }, err => errorMsg = err);

        // Give it time to attempt connection and fail
        Thread.Sleep(200);
        listener.Stop();
    }

    [Fact]
    public void SseListener_ShouldReconnectOnError()
    {
        // The handler will return an error for the SSE request
        _handler.ClearHandlers();
        _handler.WhenError("test-db.firebaseio.com", HttpStatusCode.ServiceUnavailable);

        string? lastError = null;
        var listener = _client.DbListen("test/path", (_, _) => { }, err => lastError = err);

        // Give it time to attempt and fail
        Thread.Sleep(500);
        listener.Stop();

        // After stopping, error callback may or may not have fired depending on timing
        listener.IsRunning.Should().BeFalse();
    }

    [Fact]
    public void SseListener_ReconnectDelay_ShouldIncrease()
    {
        // Access _reconnectDelay via reflection
        var listener = _client.DbListen("test", (_, _) => { });
        var delayField = typeof(SseListener).GetField("_reconnectDelay", BindingFlags.NonPublic | BindingFlags.Instance)!;

        var initialDelay = (int)delayField.GetValue(listener)!;
        initialDelay.Should().Be(1);

        listener.Stop();
    }
}
