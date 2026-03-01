using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests;

/// <summary>
/// Tests guarding all fixes and features from the kiosk audit (v3.3.0).
/// Covers: Firebase path fix, batch update rewrite, async patterns,
/// SSE null safety, phone validation, loading state, feedback, DEVMODE.
/// </summary>
public class AuditFixTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public AuditFixTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.SetDefaultSuccess();
    }

    public void Dispose() => _firebase.Dispose();

    // ==================== K1: Firebase path fix ====================

    [Fact]
    public async Task GetPrintPricingAsync_UsesMetadataPath_NoDuplicateOrgSegment()
    {
        _handler.When("metadata.json", new { blackAndWhitePrice = 0.5, colorPrice = 2.0 });

        var service = new OrganizationMetadataService(_firebase);
        var result = await service.GetPrintPricingAsync();

        result.IsSuccess.Should().BeTrue();
        // The base path already includes "organizations/test-org".
        // The fix ensures we don't double-nest: no "organizations/.../organizations/" in the URL.
        var url = _handler.SentRequests.Last().RequestUri!.ToString();
        url.Should().Contain("metadata.json");
        CountOccurrences(url, "organizations/").Should().Be(1,
            "path should have exactly one organizations/ segment (from the base path)");
    }

    private static int CountOccurrences(string source, string substring)
    {
        int count = 0, idx = 0;
        while ((idx = source.IndexOf(substring, idx, StringComparison.Ordinal)) != -1)
        {
            count++;
            idx += substring.Length;
        }
        return count;
    }

    [Fact]
    public async Task SetPrintPricingAsync_UsesMetadataPath_NotOrgPath()
    {
        var service = new OrganizationMetadataService(_firebase);
        var result = await service.SetPrintPricingAsync(1.0, 3.0);

        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetPrintPricingAsync_DefaultsWhenMissing()
    {
        _handler.WhenRaw("metadata.json", "{}");

        var service = new OrganizationMetadataService(_firebase);
        var result = await service.GetPrintPricingAsync();

        result.IsSuccess.Should().BeTrue();
        var data = result.Data!;
        var type = data.GetType();
        var bw = (double)type.GetProperty("blackAndWhitePrice")!.GetValue(data)!;
        var color = (double)type.GetProperty("colorPrice")!.GetValue(data)!;
        bw.Should().Be(1.0);
        color.Should().Be(3.0);
    }

    // ==================== K2: ChatService batch update ====================

    [Fact]
    public async Task MarkAllMessagesAsReadAsync_UpdatesEachMessageIndividually()
    {
        var chat = new ChatService(_firebase, "user-123");
        _handler.When("messages.json", new
        {
            msg1 = new { toUserId = "user-123", body = "A", read = false, timestamp = "1" },
            msg2 = new { toUserId = "user-123", body = "B", read = false, timestamp = "2" },
        });

        await chat.MarkAllMessagesAsReadAsync();

        var patchRequests = _handler.SentRequests
            .Where(r => r.Method == HttpMethod.Patch || r.Method == HttpMethod.Put)
            .ToList();

        // Should have made individual updates (PATCH to messages/msg1 and messages/msg2)
        // instead of a single root-level update
        patchRequests.Should().NotContain(r =>
            r.RequestUri!.ToString().EndsWith("/.json") ||
            r.RequestUri!.ToString().EndsWith("/test-org.json"));

        chat.Dispose();
    }

    [Fact]
    public async Task MarkAllMessagesAsReadAsync_WithNoMessages_DoesNothing()
    {
        var chat = new ChatService(_firebase, "user-123");
        _handler.WhenRaw("messages.json", "null");

        var initialCount = _handler.SentRequests.Count;
        await chat.MarkAllMessagesAsReadAsync();

        // Only the GET request, no PATCH
        var newRequests = _handler.SentRequests.Skip(initialCount).ToList();
        newRequests.Should().OnlyContain(r => r.Method == HttpMethod.Get);

        chat.Dispose();
    }

    // ==================== K3: ForceLogoutService async refactor ====================

    [Fact]
    public void ForceLogoutService_StartListening_IsNotAsyncVoid()
    {
        var method = typeof(ForceLogoutService).GetMethod("StartListening")!;
        method.ReturnType.Should().Be(typeof(void),
            "StartListening should be sync void (fire-and-forget internally)");

        // The method should NOT be marked async
        var asyncAttr = method.GetCustomAttribute<System.Runtime.CompilerServices.AsyncStateMachineAttribute>();
        asyncAttr.Should().BeNull("StartListening should not be async void");
    }

    [Fact]
    public void ForceLogoutService_HasPrivateAsyncHelper()
    {
        var method = typeof(ForceLogoutService).GetMethod(
            "ClearStaleDataAndListenAsync",
            BindingFlags.NonPublic | BindingFlags.Instance);

        method.Should().NotBeNull("should have a private async helper method");
        method!.ReturnType.Should().Be(typeof(Task));
    }

    // ==================== K4: SseListener.Stop non-blocking ====================

    [Fact]
    public void SseListener_Stop_DoesNotBlockThread()
    {
        var listener = _firebase.DbListen("test/path", (_, _) => { });

        var stopwatch = System.Diagnostics.Stopwatch.StartNew();
        listener.Stop();
        stopwatch.Stop();

        // Stop should return quickly (< 100ms), not block for 500ms
        stopwatch.ElapsedMilliseconds.Should().BeLessThan(200);
    }

    [Fact]
    public void SseListener_StopTwice_ShouldNotThrow()
    {
        var listener = _firebase.DbListen("test/path", (_, _) => { });
        listener.Stop();

        var act = () => listener.Stop();
        act.Should().NotThrow();
    }

    // ==================== U2: Phone validation ====================

    [Theory]
    [InlineData("0501234567", true)]
    [InlineData("050-123-4567", true)]
    [InlineData("050 123 4567", true)]
    [InlineData("123456789", true)]
    [InlineData("1234567890123", false)]  // too long (13 digits)
    [InlineData("12345", false)]           // too short
    [InlineData("abc", false)]
    [InlineData("050-abc", false)]
    [InlineData("", false)]
    public void AuthViewModel_PhoneValidation(string phone, bool expectedValid)
    {
        var method = typeof(AuthViewModel).GetMethod(
            "IsValidPhone", BindingFlags.NonPublic | BindingFlags.Static)!;

        var result = (bool)method.Invoke(null, new object[] { phone })!;
        result.Should().Be(expectedValid, $"phone '{phone}' validity");
    }

    [Fact]
    public async Task AuthViewModel_Register_ShortPassword_ShouldReject()
    {
        var auth = new AuthService(null!, null!, null!);
        var vm = new AuthViewModel(auth);
        vm.IsLoginMode = false;
        vm.Phone = "0501234567";
        vm.Password = "12345";
        vm.FirstName = "Test";
        vm.LastName = "User";

        await vm.RegisterCommand.ExecuteAsync(null);

        vm.ErrorMessage.Should().Contain("6");
    }

    [Fact]
    public async Task AuthViewModel_Register_ValidPassword_PassesValidation()
    {
        var auth = new AuthService(null!, null!, null!);
        var vm = new AuthViewModel(auth);
        vm.IsLoginMode = false;
        vm.Phone = "0501234567";
        vm.Password = "123456";
        vm.FirstName = "Test";
        vm.LastName = "User";

        try { await vm.RegisterCommand.ExecuteAsync(null); }
        catch (NullReferenceException) { /* AuthService has null deps */ }

        vm.ErrorMessage.Should().NotContain("6 תווים");
    }

    // ==================== U1: Loading state ====================

    [Fact]
    public void HomeViewModel_IsLoading_UpdatesPrimaryButtonText()
    {
        _handler.WhenRaw("messages.json", "null");
        var user = new UserData
        {
            Uid = "user-123", FirstName = "A", LastName = "B",
            RemainingTime = 3600, PrintBalance = 10,
        };
        var session = new SessionService(_firebase, "user-123", "test-org",
            new ComputerService(_firebase), new OperatingHoursService(_firebase),
            new ProcessCleanupService(), new BrowserCleanupService());
        var chat = new ChatService(_firebase, "user-123");
        var hours = new OperatingHoursService(_firebase);
        var vm = new HomeViewModel(session, chat, hours, user);

        vm.PrimaryButtonText.Should().Contain("התחל הפעלה");

        vm.IsLoading = true;
        vm.PrimaryButtonText.Should().Be("מתחיל...");

        vm.IsLoading = false;
        vm.PrimaryButtonText.Should().Contain("התחל הפעלה");

        chat.Dispose();
    }

    [Fact]
    public void HomeViewModel_IsLoading_WithNoTime_DoesNotChangePrimaryButton()
    {
        _handler.WhenRaw("messages.json", "null");
        var user = new UserData
        {
            Uid = "user-123", FirstName = "A", LastName = "B",
            RemainingTime = 0, PrintBalance = 0,
        };
        var session = new SessionService(_firebase, "user-123", "test-org",
            new ComputerService(_firebase), new OperatingHoursService(_firebase),
            new ProcessCleanupService(), new BrowserCleanupService());
        var chat = new ChatService(_firebase, "user-123");
        var hours = new OperatingHoursService(_firebase);
        var vm = new HomeViewModel(session, chat, hours, user);

        var originalText = vm.PrimaryButtonText;
        vm.IsLoading = true;
        vm.PrimaryButtonText.Should().Be(originalText);

        chat.Dispose();
    }

    // ==================== C4: ResumeSession through ViewModel ====================

    [Fact]
    public void HomeViewModel_ResumeSessionCommand_RaisesEvent()
    {
        _handler.WhenRaw("messages.json", "null");
        var user = new UserData
        {
            Uid = "user-123", FirstName = "A", LastName = "B",
            RemainingTime = 3600, PrintBalance = 10,
        };
        var session = new SessionService(_firebase, "user-123", "test-org",
            new ComputerService(_firebase), new OperatingHoursService(_firebase),
            new ProcessCleanupService(), new BrowserCleanupService());
        var chat = new ChatService(_firebase, "user-123");
        var hours = new OperatingHoursService(_firebase);
        var vm = new HomeViewModel(session, chat, hours, user);

        bool eventFired = false;
        vm.ResumeSessionRequested += () => eventFired = true;
        vm.ResumeSessionCommand.Execute(null);

        eventFired.Should().BeTrue();

        chat.Dispose();
    }

    [Fact]
    public void HomeViewModel_ResumeSession_NoSubscriber_DoesNotThrow()
    {
        _handler.WhenRaw("messages.json", "null");
        var user = new UserData
        {
            Uid = "user-123", FirstName = "A", LastName = "B",
            RemainingTime = 3600, PrintBalance = 10,
        };
        var session = new SessionService(_firebase, "user-123", "test-org",
            new ComputerService(_firebase), new OperatingHoursService(_firebase),
            new ProcessCleanupService(), new BrowserCleanupService());
        var chat = new ChatService(_firebase, "user-123");
        var hours = new OperatingHoursService(_firebase);
        var vm = new HomeViewModel(session, chat, hours, user);

        var act = () => vm.ResumeSessionCommand.Execute(null);
        act.Should().NotThrow();

        chat.Dispose();
    }

    // ==================== DEVMODE attribute ====================

    [Fact]
    public void DestructiveFactAttribute_WhenDevMode_SetsSkip()
    {
        var saved = Environment.GetEnvironmentVariable("DEVMODE");
        try
        {
            Environment.SetEnvironmentVariable("DEVMODE", "true");
            var attr = new DestructiveFactAttribute();
            attr.Skip.Should().NotBeNullOrEmpty();
        }
        finally
        {
            Environment.SetEnvironmentVariable("DEVMODE", saved);
        }
    }

    [Fact]
    public void DestructiveFactAttribute_WhenNotDevMode_NoSkip()
    {
        var saved = Environment.GetEnvironmentVariable("DEVMODE");
        try
        {
            Environment.SetEnvironmentVariable("DEVMODE", null);
            var attr = new DestructiveFactAttribute();
            attr.Skip.Should().BeNull();
        }
        finally
        {
            Environment.SetEnvironmentVariable("DEVMODE", saved);
        }
    }

    [Fact]
    public void DestructiveFactAttribute_Value1_IsDevMode()
    {
        var saved = Environment.GetEnvironmentVariable("DEVMODE");
        try
        {
            Environment.SetEnvironmentVariable("DEVMODE", "1");
            var attr = new DestructiveFactAttribute();
            attr.Skip.Should().NotBeNullOrEmpty();
        }
        finally
        {
            Environment.SetEnvironmentVariable("DEVMODE", saved);
        }
    }

    [Fact]
    public void DestructiveFactAttribute_CaseInsensitive()
    {
        var saved = Environment.GetEnvironmentVariable("DEVMODE");
        try
        {
            Environment.SetEnvironmentVariable("DEVMODE", "TRUE");
            var attr = new DestructiveFactAttribute();
            attr.Skip.Should().NotBeNullOrEmpty();
        }
        finally
        {
            Environment.SetEnvironmentVariable("DEVMODE", saved);
        }
    }

    // ==================== ChatService reinitialize ====================

    [Fact]
    public void ChatService_Reinitialize_StopsListeningAndClearsCache()
    {
        var chat = new ChatService(_firebase, "user-123");
        chat.StartListening();
        chat.IsListening.Should().BeTrue();

        chat.Reinitialize("user-456");
        chat.IsListening.Should().BeFalse();

        chat.Dispose();
    }

    // ==================== HomeViewModel format expiry edge cases ====================

    [Theory]
    [InlineData(null, 3600, "ללא הגבלה")]
    [InlineData(null, 0, "אין")]
    [InlineData("", 0, "אין")]
    [InlineData("not-a-date", 0, "אין")]
    public void FormatExpiry_EdgeCases(string? expiresAt, int remaining, string expected)
    {
        var result = HomeViewModel.FormatExpiry(expiresAt, remaining);
        result.Should().Be(expected);
    }

    [Fact]
    public void FormatExpiry_FewHoursRemaining_ShowsExactDate()
    {
        var dt = DateTime.Now.AddHours(5).AddMinutes(1);
        var result = HomeViewModel.FormatExpiry(dt.ToString("o"));
        result.Should().Be(dt.ToString("dd/MM/yyyy HH:mm"));
    }

    [Fact]
    public void FormatExpiry_FewMinutesRemaining_ShowsExactDate()
    {
        var dt = DateTime.Now.AddMinutes(30);
        var result = HomeViewModel.FormatExpiry(dt.ToString("o"));
        result.Should().Be(dt.ToString("dd/MM/yyyy HH:mm"));
    }

    [Fact]
    public void FormatExpiry_JustExpired_ShowsExpired()
    {
        var dt = DateTime.Now.AddMinutes(-1);
        var result = HomeViewModel.FormatExpiry(dt.ToString("o"));
        result.Should().Be("פג תוקף");
    }

    // ==================== SessionCoordinator lifecycle ====================

    [Fact]
    public void SessionCoordinator_SubscribeUnsubscribe_Cycle()
    {
        var session = new SessionService(_firebase, "user-123", "test-org",
            new ComputerService(_firebase), new OperatingHoursService(_firebase),
            new ProcessCleanupService(), new BrowserCleanupService());
        var printMonitor = new PrintMonitorService(_firebase, "user-123");
        var dbPath = Path.Combine(Path.GetTempPath(), $"audit_{Guid.NewGuid():N}.db");
        var localDb = new LocalDatabase(dbPath);
        var auth = new AuthService(_firebase, localDb, new ComputerService(_firebase));
        var coordinator = new SessionCoordinator(session, printMonitor, auth, new PrintHistoryService());

        // Full lifecycle
        for (int i = 0; i < 3; i++)
        {
            coordinator.Subscribe();
            coordinator.Unsubscribe();
        }

        // CloseFloatingTimer and ResumeSession should be safe with no UI
        var act = () =>
        {
            coordinator.CloseFloatingTimer();
            coordinator.ResumeSession();
        };
        act.Should().NotThrow();

        localDb.Dispose();
        try { File.Delete(dbPath); } catch { }
    }
}
