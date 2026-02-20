using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class HomeViewModelTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public HomeViewModelTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        // Default handler returns empty messages
        _handler.WhenRaw("messages.json", "null");
    }

    public void Dispose() => _firebase.Dispose();

    private HomeViewModel CreateVm(UserData? user = null, int remainingTime = 3600)
    {
        var userData = user ?? new UserData
        {
            Uid = "user-123",
            FirstName = "David",
            LastName = "Cohen",
            RemainingTime = remainingTime,
            PrintBalance = 15.50,
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
    public void InitialState_ShouldShowWelcomeMessage()
    {
        var vm = CreateVm();
        vm.WelcomeMessage.Should().Contain("David");
        vm.WelcomeMessage.Should().Contain("שלום");
    }

    [Fact]
    public void InitialState_ShouldShowFormattedTime()
    {
        var vm = CreateVm(remainingTime: 3661); // 1h 1m 1s
        vm.RemainingTime.Should().Be("01:01:01");
    }

    [Fact]
    public void InitialState_ShouldShowFormattedPrintBalance()
    {
        var vm = CreateVm();
        vm.PrintBalance.Should().Contain("15.50");
        vm.PrintBalance.Should().Contain("₪");
    }

    [Fact]
    public void IsSessionActive_Initially_ShouldBeFalse()
    {
        var vm = CreateVm();
        vm.IsSessionActive.Should().BeFalse();
    }

    [Fact]
    public void IsSessionInactive_ShouldInvertIsSessionActive()
    {
        var vm = CreateVm();
        vm.IsSessionInactive.Should().BeTrue();

        vm.IsSessionActive = true;
        vm.IsSessionInactive.Should().BeFalse();
    }

    [Fact]
    public void PropertyChanged_ShouldFireForIsSessionActive()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.IsSessionActive = true;

        changed.Should().Contain("IsSessionActive");
        changed.Should().Contain("IsSessionInactive"); // Derived property
    }

    [Fact]
    public void InitialState_WithZeroTime_ShouldShowZero()
    {
        var vm = CreateVm(remainingTime: 0);
        vm.RemainingTime.Should().Be("00:00:00");
    }

    [Fact]
    public void PropertyChanged_ShouldFireForLoadingAndError()
    {
        var vm = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.IsLoading = true;
        vm.ErrorMessage = "test error";
        vm.UnreadMessages = 5;

        changed.Should().Contain("IsLoading");
        changed.Should().Contain("ErrorMessage");
        changed.Should().Contain("UnreadMessages");
    }
}
