using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class HomeViewModelCoverageTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public HomeViewModelCoverageTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.WhenRaw("messages.json", "null");
    }

    public void Dispose() => _firebase.Dispose();

    private HomeViewModel CreateVm(UserData? user = null)
    {
        var userData = user ?? new UserData
        {
            Uid = "user-123",
            FirstName = "Test",
            LastName = "User",
            RemainingTime = 3600,
            PrintBalance = 10.0,
        };
        var session = new SessionService(_firebase, "user-123", "test-org",
            new ComputerService(_firebase),
            new OperatingHoursService(_firebase),
            new ProcessCleanupService(),
            new BrowserCleanupService());
        var chat = new ChatService(_firebase, "user-123");
        var hours = new OperatingHoursService(_firebase);
        return new HomeViewModel(session, chat, hours, userData);
    }

    [Fact]
    public void WelcomeMessage_ContainsFullName()
    {
        var vm = CreateVm(new UserData { FirstName = "Alice", LastName = "Smith", Uid = "u1" });
        vm.WelcomeMessage.Should().Contain("Alice");
        vm.WelcomeMessage.Should().Contain("Smith");
    }

    [Fact]
    public void InitialState_ErrorMessageIsEmpty()
    {
        var vm = CreateVm();
        vm.ErrorMessage.Should().BeEmpty();
    }

    [Fact]
    public void InitialState_IsLoadingIsFalse()
    {
        var vm = CreateVm();
        vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public void InitialState_IsEndingSessionIsFalse()
    {
        var vm = CreateVm();
        vm.IsEndingSession.Should().BeFalse();
    }

    [Fact]
    public void PrintBalance_FormattedCorrectly()
    {
        var vm = CreateVm(new UserData
        {
            Uid = "u1",
            FirstName = "A",
            LastName = "B",
            PrintBalance = 123.45
        });
        vm.PrintBalance.Should().Be("123.45 ₪");
    }

    [Fact]
    public void PrintBalance_Zero()
    {
        var vm = CreateVm(new UserData
        {
            Uid = "u1",
            FirstName = "A",
            LastName = "B",
            PrintBalance = 0
        });
        vm.PrintBalance.Should().Be("0.00 ₪");
    }

    [Fact]
    public void RemainingTime_LargeValue()
    {
        var vm = CreateVm(new UserData
        {
            Uid = "u1",
            FirstName = "A",
            LastName = "B",
            RemainingTime = 86400
        });
        vm.RemainingTime.Should().NotBeEmpty();
    }

    [Fact]
    public void TimeExpiry_NullExpiry_ShowsUnlimited()
    {
        var vm = CreateVm(new UserData
        {
            Uid = "u1",
            FirstName = "A",
            LastName = "B",
            TimeExpiresAt = null
        });
        vm.TimeExpiry.Should().Be("ללא הגבלה");
    }

    [Fact]
    public void TimeExpiry_FutureExpiry_ShowsDays()
    {
        var vm = CreateVm(new UserData
        {
            Uid = "u1",
            FirstName = "A",
            LastName = "B",
            TimeExpiresAt = DateTime.Now.AddDays(5).AddMinutes(1).ToString("o")
        });
        vm.TimeExpiry.Should().Contain("ימים");
    }

    [Fact]
    public void TimeExpiry_PastExpiry_ShowsExpired()
    {
        var vm = CreateVm(new UserData
        {
            Uid = "u1",
            FirstName = "A",
            LastName = "B",
            TimeExpiresAt = DateTime.Now.AddDays(-1).ToString("o")
        });
        vm.TimeExpiry.Should().Be("פג תוקף");
    }

    [Fact]
    public void Dispose_DoesNotThrow()
    {
        var vm = CreateVm();
        var act = () => vm.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_MultipleTimes_DoesNotThrow()
    {
        var vm = CreateVm();
        vm.Dispose();
        var act = () => vm.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void ViewMessagesRequested_EventSubscription()
    {
        var vm = CreateVm();
        bool fired = false;
        vm.ViewMessagesRequested += () => fired = true;

        vm.UnreadMessages = 3;
        vm.ViewMessagesCommand.Execute(null);

        fired.Should().BeTrue();
    }

    [Fact]
    public void ViewMessages_NoUnread_DoesNotFire()
    {
        var vm = CreateVm();
        bool fired = false;
        vm.ViewMessagesRequested += () => fired = true;

        vm.UnreadMessages = 0;
        vm.ViewMessagesCommand.Execute(null);

        fired.Should().BeFalse();
    }

    [Fact]
    public void IsSessionInactive_TracksActive()
    {
        var vm = CreateVm();
        vm.IsSessionActive.Should().BeFalse();
        vm.IsSessionInactive.Should().BeTrue();

        vm.IsSessionActive = true;
        vm.IsSessionInactive.Should().BeFalse();

        vm.IsSessionActive = false;
        vm.IsSessionInactive.Should().BeTrue();
    }

    [Fact]
    public void StartSessionCommand_WithNoTime_SetsError()
    {
        var vm = CreateVm(new UserData
        {
            Uid = "u1",
            FirstName = "A",
            LastName = "B",
            RemainingTime = 0,
        });

        vm.StartSessionCommand.Execute(null);
        Thread.Sleep(200);

        vm.ErrorMessage.Should().NotBeEmpty();
    }

    [Fact]
    public void UnreadMessages_CanBeSet()
    {
        var vm = CreateVm();
        vm.UnreadMessages = 5;
        vm.UnreadMessages.Should().Be(5);
    }
}
