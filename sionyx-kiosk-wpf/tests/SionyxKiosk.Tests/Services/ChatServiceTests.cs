using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ChatServiceTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ChatService _service;

    public ChatServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _service = new ChatService(_firebase, "user-123");
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    // ==================== LISTENING ====================

    [Fact]
    public void IsListening_Initially_ShouldBeFalse()
    {
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public void StartListening_ShouldSetIsListening()
    {
        _service.StartListening();
        _service.IsListening.Should().BeTrue();
        _service.StopListening(); // cleanup
    }

    [Fact]
    public void StopListening_AfterStart_ShouldUnsetIsListening()
    {
        _service.StartListening();
        _service.StopListening();
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public void StopListening_WithoutStart_ShouldNotThrow()
    {
        var act = () => _service.StopListening();
        act.Should().NotThrow();
    }

    [Fact]
    public void StartListening_Twice_ShouldBeIdempotent()
    {
        _service.StartListening();
        _service.StartListening(); // Should not throw
        _service.IsListening.Should().BeTrue();
        _service.StopListening();
    }

    // ==================== CACHE ====================

    [Fact]
    public void InvalidateCache_ShouldClearMessages()
    {
        _service.InvalidateCache();
        // Should not throw and should reset state
    }

    // ==================== MESSAGES ====================

    [Fact]
    public async Task GetUnreadMessagesAsync_WithMessages_ShouldReturnFiltered()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Hello", read = false, timestamp = "2026-01-01T10:00:00" },
            msg2 = new { toUserId = "other-user", body = "Not for you", read = false, timestamp = "2026-01-01T10:00:00" },
            msg3 = new { toUserId = "user-123", body = "Read message", read = true, timestamp = "2026-01-01T10:00:00" },
        });

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();
        var messages = (List<Dictionary<string, object?>>)result.Data!;
        messages.Count.Should().Be(1);
        messages[0]["body"].Should().Be("Hello");
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WhenEmpty_ShouldReturnEmptyList()
    {
        _handler.WhenRaw("messages.json", "null");

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();
        var messages = (List<Dictionary<string, object?>>)result.Data!;
        messages.Count.Should().Be(0);
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("messages.json");

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task MarkMessageAsReadAsync_ShouldNotThrow()
    {
        _handler.SetDefaultSuccess();

        var result = await _service.MarkMessageAsReadAsync("msg-123");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task MarkAllMessagesAsReadAsync_ShouldNotThrow()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Hello", read = false, timestamp = "2026-01-01T10:00:00" },
        });
        _handler.SetDefaultSuccess();

        await _service.MarkAllMessagesAsReadAsync();
    }

    [Fact]
    public async Task UpdateLastSeenAsync_ShouldNotThrow()
    {
        _handler.SetDefaultSuccess();
        await _service.UpdateLastSeenAsync(force: true);
    }

    [Fact]
    public async Task UpdateLastSeenAsync_WhenDebounced_ShouldSkip()
    {
        _handler.SetDefaultSuccess();
        await _service.UpdateLastSeenAsync(force: true);
        // Second call within debounce window should be a no-op
        await _service.UpdateLastSeenAsync(force: false);
    }

    // ==================== DISPOSE ====================

    [Fact]
    public void Dispose_ShouldStopListeningAndClearCache()
    {
        _service.StartListening();
        _service.Dispose();
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_ShouldSortByTimestamp()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Second", read = false, timestamp = "2026-01-02T10:00:00" },
            msg2 = new { toUserId = "user-123", body = "First", read = false, timestamp = "2026-01-01T10:00:00" },
        });

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        var messages = (List<Dictionary<string, object?>>)result.Data!;
        messages[0]["body"].Should().Be("First");
        messages[1]["body"].Should().Be("Second");
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_ShouldExtractMessageFields()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "Hello", fromName = "Admin", read = false, timestamp = "2026-01-01T10:00:00" },
        });

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        var msg = ((List<Dictionary<string, object?>>)result.Data!)[0];
        msg["id"].Should().Be("msg1");
        msg["body"].Should().Be("Hello");
        msg["fromName"].Should().Be("Admin");
    }
}
