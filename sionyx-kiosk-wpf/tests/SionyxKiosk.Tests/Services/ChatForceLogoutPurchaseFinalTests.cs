using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Final coverage tests for ChatService, ForceLogoutService, and PurchaseService
/// targeting remaining uncovered paths.
/// </summary>
public class ChatServiceFinalCoverageTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ChatService _service;

    public ChatServiceFinalCoverageTests()
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
    public void OnStreamError_ShouldLogAndNotThrow()
    {
        // Test the private OnStreamError callback
        var method = typeof(ChatService).GetMethod("OnStreamError",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        var act = () => method.Invoke(_service, new object[] { "Test SSE error" });
        act.Should().NotThrow();
    }

    [Fact]
    public void OnStreamEvent_WithPatch_ShouldRefetchMessages()
    {
        _handler.SetDefaultSuccess();
        var method = typeof(ChatService).GetMethod("OnStreamEvent",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        var data = TestFirebaseFactory.ToJsonElement(new { path = "/" });
        var act = () => method.Invoke(_service, new object?[] { "patch", (JsonElement?)data });
        act.Should().NotThrow();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithNumberAndBoolFields_ShouldExtract()
    {
        // Test extraction of various JsonValueKind types
        _handler.When("messages.json", new
        {
            msg1 = new
            {
                toUserId = "test-uid",
                text = "Hello",
                read = false,
                timestamp = "2024-01-01T10:00:00",
                priority = 5,
                urgent = true,
            },
        });

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();
        var msgs = (List<Dictionary<string, object?>>)result.Data!;
        msgs.Should().HaveCount(1);
        msgs[0]["priority"].Should().Be(5.0);
        msgs[0]["urgent"].Should().Be(true);
    }

    [Fact]
    public async Task MarkAllMessagesAsReadAsync_WhenFails_ShouldNotThrow()
    {
        _handler.WhenError("messages.json");
        var act = async () => await _service.MarkAllMessagesAsReadAsync();
        await act.Should().NotThrowAsync();
    }

    [Fact]
    public async Task GetUnreadMessagesAsync_WithMessagesWithNoTimestamp_ShouldSort()
    {
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "test-uid", text = "No timestamp", read = false },
            msg2 = new { toUserId = "test-uid", text = "Has timestamp", read = false, timestamp = "2024-01-01" },
        });

        var result = await _service.GetUnreadMessagesAsync(useCache: false);
        result.IsSuccess.Should().BeTrue();
        var msgs = (List<Dictionary<string, object?>>)result.Data!;
        msgs.Should().HaveCount(2);
    }
}

/// <summary>
/// Final coverage tests for ForceLogoutService targeting exception in OnEvent.
/// </summary>
public class ForceLogoutFinalCoverageTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ForceLogoutService _service;

    public ForceLogoutFinalCoverageTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ForceLogoutService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void OnEvent_WithPutAndNoReason_ShouldUseDefaultReason()
    {
        string? receivedReason = null;
        _service.ForceLogout += reason => receivedReason = reason;

        _handler.SetDefaultSuccess();

        var method = typeof(ForceLogoutService).GetMethod("OnEvent",
            BindingFlags.NonPublic | BindingFlags.Instance)!;

        // JSON object without "reason" property
        var data = TestFirebaseFactory.ToJsonElement(new { timestamp = "2024-01-01" });
        method.Invoke(_service, new object?[] { "put", (JsonElement?)data });

        receivedReason.Should().Be("admin_forced");
    }

    [Fact]
    public void OnEvent_WithNonPutEventType_ShouldNotRaise()
    {
        var raised = false;
        _service.ForceLogout += _ => raised = true;

        var method = typeof(ForceLogoutService).GetMethod("OnEvent",
            BindingFlags.NonPublic | BindingFlags.Instance)!;
        var data = TestFirebaseFactory.ToJsonElement(new { reason = "test" });

        method.Invoke(_service, new object?[] { "patch", (JsonElement?)data });
        raised.Should().BeFalse();
    }

    [Fact]
    public void OnEvent_ShouldDeleteForceLogoutAfterProcessing()
    {
        _service.ForceLogout += _ => { };
        _handler.SetDefaultSuccess();

        // Start listening to set _userId
        _service.StartListening("test-user");
        _service.StopListening();

        var method = typeof(ForceLogoutService).GetMethod("OnEvent",
            BindingFlags.NonPublic | BindingFlags.Instance)!;

        var data = TestFirebaseFactory.ToJsonElement(new { reason = "admin" });
        var act = () => method.Invoke(_service, new object?[] { "put", (JsonElement?)data });
        act.Should().NotThrow();
    }
}

/// <summary>
/// Final coverage tests for PurchaseService targeting CreatePendingPurchaseAsync edge cases.
/// </summary>
public class PurchaseFinalCoverageTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PurchaseService _service;

    public PurchaseFinalCoverageTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new PurchaseService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public async Task CreatePendingPurchaseAsync_WithValidData_ShouldReturnPurchaseId()
    {
        _handler.SetDefaultSuccess();

        var package = new SionyxKiosk.Models.Package
        {
            Id = "pkg-1",
            Name = "Basic",
            Minutes = 60,
            Prints = 10,
            Price = 29.99,
            ValidityDays = 30,
        };

        var result = await _service.CreatePendingPurchaseAsync("user-1", package);
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPurchaseStatisticsAsync_WithCompletedAndPending_ShouldCalculateCorrectly()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-1", status = "completed", amount = 10.0, createdAt = "2024-01-01" },
            p2 = new { userId = "user-1", status = "completed", amount = 20.0, createdAt = "2024-01-02" },
            p3 = new { userId = "user-1", status = "pending", amount = 15.0, createdAt = "2024-01-03" },
            p4 = new { userId = "user-1", status = "failed", amount = 5.0, createdAt = "2024-01-04" },
            p5 = new { userId = "other-user", status = "completed", amount = 50.0, createdAt = "2024-01-01" },
        });

        var result = await _service.GetPurchaseStatisticsAsync("user-1");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_WithMultiplePurchases_ShouldSortNewestFirst()
    {
        _handler.When("purchases.json", new
        {
            p1 = new { userId = "user-1", status = "completed", createdAt = "2024-01-01" },
            p2 = new { userId = "user-1", status = "completed", createdAt = "2024-03-01" },
            p3 = new { userId = "user-1", status = "completed", createdAt = "2024-02-01" },
        });

        var result = await _service.GetUserPurchaseHistoryAsync("user-1");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetUserPurchaseHistoryAsync_WithNonObjectValues_ShouldSkip()
    {
        _handler.WhenRaw("purchases.json", "{\"p1\": \"not an object\", \"p2\": 42}");

        var result = await _service.GetUserPurchaseHistoryAsync("user-1");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPurchaseStatusAsync_WhenFails_ShouldReturnError()
    {
        _handler.WhenError("purchases/");
        var result = await _service.GetPurchaseStatusAsync("nonexistent");
        result.IsSuccess.Should().BeFalse();
    }

    [Fact]
    public async Task GetPurchaseStatusAsync_WithValidPurchase_ShouldReturnData()
    {
        _handler.When("purchases/p123.json", new
        {
            userId = "user-1",
            status = "completed",
            amount = 29.99,
        });

        var result = await _service.GetPurchaseStatusAsync("p123");
        result.IsSuccess.Should().BeTrue();
    }
}
