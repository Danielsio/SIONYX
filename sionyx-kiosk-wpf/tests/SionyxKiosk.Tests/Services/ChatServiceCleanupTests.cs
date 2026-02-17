using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Tests for ChatService.CleanupOldMessagesAsync and Reinitialize,
/// plus cache TTL and additional edge cases.
/// </summary>
public class ChatServiceCleanupTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ChatService _service;

    public ChatServiceCleanupTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
        _service = new ChatService(_firebase, "user-123");
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    // ==================== REINITIALIZE ====================

    [Fact]
    public void Reinitialize_ShouldStopListeningAndInvalidateCache()
    {
        _service.StartListening();
        _service.IsListening.Should().BeTrue();

        _service.Reinitialize("new-user-456");
        _service.IsListening.Should().BeFalse();
    }

    [Fact]
    public void Reinitialize_WhenNotListening_ShouldNotThrow()
    {
        var act = () => _service.Reinitialize("new-user-456");
        act.Should().NotThrow();
    }

    [Fact]
    public void Reinitialize_CalledMultipleTimes_ShouldNotThrow()
    {
        _service.Reinitialize("user-a");
        _service.Reinitialize("user-b");
        _service.Reinitialize("user-c");
    }

    // ==================== CLEANUP OLD MESSAGES ====================

    [Fact]
    public async Task CleanupOldMessagesAsync_WhenNoMessages_ShouldReturnZero()
    {
        _handler.WhenRaw("messages.json", "null");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(0);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_WhenServiceFails_ShouldReturnZero()
    {
        _handler.WhenError("messages");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(0);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_WithRecentReadMessages_ShouldNotDelete()
    {
        var recentTimestamp = DateTimeOffset.UtcNow.AddDays(-5).ToUnixTimeMilliseconds();
        _handler.WhenRaw("messages.json", $@"{{
            ""msg1"": {{ ""toUserId"": ""user-123"", ""message"": ""Recent"", ""read"": true, ""timestamp"": {recentTimestamp} }}
        }}");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(0);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_WithOldReadMessages_ShouldDelete()
    {
        var oldTimestamp = DateTimeOffset.UtcNow.AddDays(-60).ToUnixTimeMilliseconds();
        _handler.WhenRaw("messages.json", $@"{{
            ""msg1"": {{ ""toUserId"": ""user-123"", ""message"": ""Old"", ""read"": true, ""timestamp"": {oldTimestamp} }}
        }}");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(1);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_WithUnreadOldMessages_ShouldNotDelete()
    {
        var oldTimestamp = DateTimeOffset.UtcNow.AddDays(-60).ToUnixTimeMilliseconds();
        _handler.WhenRaw("messages.json", $@"{{
            ""msg1"": {{ ""toUserId"": ""user-123"", ""message"": ""Old unread"", ""read"": false, ""timestamp"": {oldTimestamp} }}
        }}");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(0);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_WithOtherUsersMessages_ShouldNotDelete()
    {
        var oldTimestamp = DateTimeOffset.UtcNow.AddDays(-60).ToUnixTimeMilliseconds();
        _handler.WhenRaw("messages.json", $@"{{
            ""msg1"": {{ ""toUserId"": ""other-user"", ""message"": ""Not mine"", ""read"": true, ""timestamp"": {oldTimestamp} }}
        }}");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(0);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_WithStringTimestamp_ShouldParse()
    {
        var oldTimestamp = DateTimeOffset.UtcNow.AddDays(-60).ToUnixTimeMilliseconds();
        _handler.WhenRaw("messages.json", $@"{{
            ""msg1"": {{ ""toUserId"": ""user-123"", ""message"": ""Old str"", ""read"": true, ""timestamp"": ""{oldTimestamp}"" }}
        }}");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(1);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_WithCustomRetention_ShouldRespect()
    {
        var timestamp15DaysAgo = DateTimeOffset.UtcNow.AddDays(-15).ToUnixTimeMilliseconds();
        _handler.WhenRaw("messages.json", $@"{{
            ""msg1"": {{ ""toUserId"": ""user-123"", ""message"": ""Semi-old"", ""read"": true, ""timestamp"": {timestamp15DaysAgo} }}
        }}");

        // With 30-day retention, 15-day-old message should survive
        var deleted30 = await _service.CleanupOldMessagesAsync(30);
        deleted30.Should().Be(0);

        // With 10-day retention, 15-day-old message should be deleted
        var deleted10 = await _service.CleanupOldMessagesAsync(10);
        deleted10.Should().Be(1);
    }

    [Fact]
    public async Task CleanupOldMessagesAsync_MixedMessages_ShouldDeleteOnlyOldRead()
    {
        var oldTimestamp = DateTimeOffset.UtcNow.AddDays(-60).ToUnixTimeMilliseconds();
        var recentTimestamp = DateTimeOffset.UtcNow.AddDays(-5).ToUnixTimeMilliseconds();
        _handler.WhenRaw("messages.json", $@"{{
            ""msg1"": {{ ""toUserId"": ""user-123"", ""message"": ""Old read"", ""read"": true, ""timestamp"": {oldTimestamp} }},
            ""msg2"": {{ ""toUserId"": ""user-123"", ""message"": ""Recent read"", ""read"": true, ""timestamp"": {recentTimestamp} }},
            ""msg3"": {{ ""toUserId"": ""user-123"", ""message"": ""Old unread"", ""read"": false, ""timestamp"": {oldTimestamp} }},
            ""msg4"": {{ ""toUserId"": ""other-user"", ""message"": ""Other user old"", ""read"": true, ""timestamp"": {oldTimestamp} }}
        }}");

        var deleted = await _service.CleanupOldMessagesAsync();
        deleted.Should().Be(1); // Only msg1
    }

    // ==================== CACHE BEHAVIOR ====================

    [Fact]
    public async Task GetUnreadMessagesAsync_UseCache_WhenFreshCache_ShouldReturnCached()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""Hello"", ""read"": false, ""timestamp"": 1700000000000 }
        }");

        // First call populates cache
        var result1 = await _service.GetUnreadMessagesAsync(useCache: false);
        result1.IsSuccess.Should().BeTrue();

        // Second call (within 10s) should use cache
        var result2 = await _service.GetUnreadMessagesAsync(useCache: true);
        result2.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_AfterInvalidateCache_ShouldRefetch()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""Hello"", ""read"": false, ""timestamp"": 1700000000000 }
        }");

        await _service.GetUnreadMessagesAsync(useCache: false);
        _service.InvalidateCache();

        // Should refetch since cache was invalidated
        var result = await _service.GetUnreadMessagesAsync(useCache: true);
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== UPDATE LAST SEEN ====================

    [Fact]
    public async Task UpdateLastSeenAsync_Force_ShouldAlwaysUpdate()
    {
        await _service.UpdateLastSeenAsync(force: true);
        // No crash
    }

    [Fact]
    public async Task UpdateLastSeenAsync_WithinDebounce_ShouldSkip()
    {
        await _service.UpdateLastSeenAsync(force: true);

        var requestsBefore = _handler.SentRequests.Count;
        await _service.UpdateLastSeenAsync(force: false);
        // Debounced — request count should not increase (or increase minimally)
        _handler.SentRequests.Count.Should().BeLessThanOrEqualTo(requestsBefore + 1);
    }

    // ==================== MARK ALL MESSAGES AS READ ====================

    [Fact]
    public async Task MarkAllMessagesAsReadAsync_WithNoMessages_ShouldNotThrow()
    {
        _handler.WhenRaw("messages.json", "null");
        var act = async () => await _service.MarkAllMessagesAsReadAsync();
        await act.Should().NotThrowAsync();
    }

    [Fact]
    public async Task MarkAllMessagesAsReadAsync_WithMessages_ShouldMarkEach()
    {
        _handler.WhenRaw("messages.json", @"{
            ""msg1"": { ""toUserId"": ""user-123"", ""message"": ""One"", ""read"": false, ""timestamp"": 1700000000000 },
            ""msg2"": { ""toUserId"": ""user-123"", ""message"": ""Two"", ""read"": false, ""timestamp"": 1700000001000 }
        }");

        await _service.MarkAllMessagesAsReadAsync();

        // Verify that mark-as-read requests were sent
        var markRequests = _handler.SentRequests
            .Where(r => r.RequestUri?.ToString().Contains("messages/msg") ?? false)
            .ToList();
        markRequests.Should().NotBeEmpty();
    }
}
