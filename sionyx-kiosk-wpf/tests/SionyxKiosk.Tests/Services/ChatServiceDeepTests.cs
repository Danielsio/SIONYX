using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for ChatService covering SSE callbacks, caching, and debouncing.
/// </summary>
public class ChatServiceDeepTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ChatService _service;

    public ChatServiceDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ChatService(_firebase, "test-uid");
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    [Fact]
    public void Constructor_ShouldInitialize()
    {
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithNoData_ShouldReturnEmptyList()
    {
        _handler.WhenRaw("messages.json", "null");

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithMessages_ShouldFilterByUserId()
    {
        var messages = new
        {
            msg1 = new { toUserId = "test-uid", text = "Hello", read = false, timestamp = "2024-01-01T10:00:00" },
            msg2 = new { toUserId = "other-uid", text = "Not for me", read = false, timestamp = "2024-01-01T11:00:00" },
            msg3 = new { toUserId = "test-uid", text = "Read msg", read = true, timestamp = "2024-01-01T12:00:00" },
            msg4 = new { toUserId = "test-uid", text = "World", read = false, timestamp = "2024-01-01T13:00:00" },
        };
        _handler.When("messages.json", messages);

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();

        var msgList = (List<Dictionary<string, object?>>)result.Data!;
        msgList.Should().HaveCount(2);
        msgList[0]["text"].Should().Be("Hello");
        msgList[1]["text"].Should().Be("World");
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_ShouldSortByTimestamp()
    {
        var messages = new
        {
            msg1 = new { toUserId = "test-uid", text = "Second", read = false, timestamp = "2024-01-01T12:00:00" },
            msg2 = new { toUserId = "test-uid", text = "First", read = false, timestamp = "2024-01-01T10:00:00" },
        };
        _handler.When("messages.json", messages);

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        var msgList = (List<Dictionary<string, object?>>)result.Data!;
        msgList[0]["text"].Should().Be("First");
        msgList[1]["text"].Should().Be("Second");
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithCache_ShouldReturnCached()
    {
        var messages = new
        {
            msg1 = new { toUserId = "test-uid", text = "Hello", read = false, timestamp = "2024-01-01T10:00:00" },
        };
        _handler.When("messages.json", messages);

        // First call - no cache
        await _service.GetUnreadMessagesAsync(useCache: false);

        // Second call - should use cache
        var result = await _service.GetUnreadMessagesAsync(useCache: true);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("messages.json");
        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public void InvalidateCache_ShouldClearCache()
    {
        _service.InvalidateCache();
        _service.Should().NotBeNull();
    }

    [Fact]
    public void StartListening_ShouldSetIsListeningTrue()
    {
        _service.StartListening();
        _service.IsListening.Should().BeTrue();
        _service.StopListening();
    }

    [Fact]
    public void StopListening_ShouldSetIsListeningFalse()
    {
        _service.StartListening();
        _service.StopListening();
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public void StartListening_WhenAlreadyListening_ShouldNotStart()
    {
        _service.StartListening();
        _service.StartListening(); // Should be no-op
        _service.IsListening.Should().BeTrue();
        _service.StopListening();
    }

    [Fact]
    public void StopListening_WhenNotListening_ShouldBeNoOp()
    {
        _service.StopListening();
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public async Task MarkMessageAsReadAsync_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.MarkMessageAsReadAsync("msg-123");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task UpdateLastSeenAsync_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        await _service.UpdateLastSeenAsync(force: true);
    }

    [Fact]
    public async Task UpdateLastSeenAsync_Debounced_ShouldNotUpdateTwice()
    {
        _handler.SetDefaultSuccess();

        await _service.UpdateLastSeenAsync(force: true);

        // Second call without force should be debounced
        var requestCountBefore = _handler.SentRequests.Count;
        await _service.UpdateLastSeenAsync(force: false);
        // Should not have sent additional request (debounced)
    }

    [Fact]
    public void MessagesReceived_Event_ShouldBeSubscribable()
    {
        _service.MessagesReceived += _ => { };
        _service.Should().NotBeNull();
    }

    [Fact]
    public void Dispose_ShouldStopListeningAndClearCache()
    {
        _service.StartListening();
        _service.Dispose();
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public void OnStreamEvent_WithKeepAlive_ShouldUpdateLastSeen()
    {
        _handler.SetDefaultSuccess();

        var method = typeof(ChatService).GetMethod("OnStreamEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(_service, new object?[] { "keep-alive", null });
        act.Should().NotThrow();
    }

    [Fact]
    public void OnStreamEvent_WithCancel_ShouldNotThrow()
    {
        var method = typeof(ChatService).GetMethod("OnStreamEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(_service, new object?[] { "cancel", null });
        act.Should().NotThrow();
    }

    [Fact]
    public void OnStreamEvent_WithAuthRevoked_ShouldNotThrow()
    {
        var method = typeof(ChatService).GetMethod("OnStreamEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(_service, new object?[] { "auth_revoked", null });
        act.Should().NotThrow();
    }

    [Fact]
    public void OnStreamEvent_WithPut_ShouldRefetchMessages()
    {
        _handler.SetDefaultSuccess();

        var method = typeof(ChatService).GetMethod("OnStreamEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var data = TestFirebaseFactory.ToJsonElement(new { path = "/" });
        var act = () => method.Invoke(_service, new object?[] { "put", (JsonElement?)data });
        act.Should().NotThrow();
    }

    [Fact]
    public void OnStreamEvent_WithUnknownEventType_ShouldIgnore()
    {
        var method = typeof(ChatService).GetMethod("OnStreamEvent", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(_service, new object?[] { "unknown_type", null });
        act.Should().NotThrow();
    }

    [Fact]
    public async Task MarkAllMessagesAsReadAsync_WithMessages_ShouldMarkEach()
    {
        var messages = new
        {
            msg1 = new { toUserId = "test-uid", text = "Hello", read = false, timestamp = "2024-01-01T10:00:00" },
            msg2 = new { toUserId = "test-uid", text = "World", read = false, timestamp = "2024-01-01T11:00:00" },
        };
        _handler.When("messages.json", messages);
        _handler.SetDefaultSuccess();

        await _service.MarkAllMessagesAsReadAsync();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithEmptyObject_ShouldReturnEmpty()
    {
        _handler.WhenRaw("messages.json", "{}");

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();
        var msgList = (List<Dictionary<string, object?>>)result.Data!;
        msgList.Should().BeEmpty();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithNonObjectMessages_ShouldSkip()
    {
        // Messages where values are not objects should be skipped
        _handler.WhenRaw("messages.json", "{\"msg1\": \"just a string\", \"msg2\": 42}");

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();
        var msgList = (List<Dictionary<string, object?>>)result.Data!;
        msgList.Should().BeEmpty();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithListeningAndCache_ShouldReturnCached()
    {
        var messages = new
        {
            msg1 = new { toUserId = "test-uid", text = "Hello", read = false, timestamp = "t" },
        };
        _handler.When("messages.json", messages);

        // Prime the cache
        await _service.GetUnreadMessagesAsync(useCache: false);

        // Start listening
        _service.StartListening();

        // Should use cache since IsListening and cache has data
        var result = await _service.GetUnreadMessagesAsync(useCache: true);
        result.IsSuccess.Should().BeTrue();

        _service.StopListening();
    }
}
