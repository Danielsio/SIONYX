using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

/// <summary>
/// Deep coverage for HomeViewModel: commands, events, dispose, edge cases.
/// </summary>
public class HomeViewModelDeepTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;

    public HomeViewModelDeepTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create("user-123");
        _handler.WhenRaw("messages.json", "null");
    }

    public void Dispose() => _firebase.Dispose();

    private (HomeViewModel Vm, SessionService Session) CreateVm(
        int remainingTime = 3600,
        double printBalance = 15.50,
        string firstName = "David",
        string lastName = "Cohen")
    {
        var user = new UserData
        {
            Uid = "user-123",
            FirstName = firstName,
            LastName = lastName,
            RemainingTime = remainingTime,
            PrintBalance = printBalance,
        };

        var session = new SessionService(_firebase, "user-123", "test-org");
        var chat = new ChatService(_firebase, "user-123");
        var hours = new OperatingHoursService(_firebase);

        var vm = new HomeViewModel(session, chat, hours, user);
        return (vm, session);
    }

    // ==================== WELCOME MESSAGE ====================

    [Fact]
    public void WelcomeMessage_ShouldContainFullName()
    {
        var (vm, _) = CreateVm(firstName: "Sarah", lastName: "Levi");
        vm.WelcomeMessage.Should().Contain("Sarah");
    }

    [Fact]
    public void WelcomeMessage_ShouldStartWithGreeting()
    {
        var (vm, _) = CreateVm();
        vm.WelcomeMessage.Should().StartWith("שלום");
    }

    // ==================== PRINT BALANCE ====================

    [Fact]
    public void PrintBalance_ZeroBalance_ShouldShowZero()
    {
        var (vm, _) = CreateVm(printBalance: 0);
        vm.PrintBalance.Should().Contain("0.00");
    }

    [Fact]
    public void PrintBalance_LargeBalance_ShouldFormat()
    {
        var (vm, _) = CreateVm(printBalance: 999.99);
        vm.PrintBalance.Should().Contain("999.99");
        vm.PrintBalance.Should().Contain("₪");
    }

    // ==================== REMAINING TIME FORMATTING ====================

    [Fact]
    public void RemainingTime_ExactlyOneHour_ShouldFormat()
    {
        var (vm, _) = CreateVm(remainingTime: 3600);
        vm.RemainingTime.Should().Be("01:00:00");
    }

    [Fact]
    public void RemainingTime_LessThanMinute_ShouldFormat()
    {
        var (vm, _) = CreateVm(remainingTime: 45);
        vm.RemainingTime.Should().Be("00:00:45");
    }

    [Fact]
    public void RemainingTime_NegativeTime_ShouldClampToZero()
    {
        var (vm, _) = CreateVm(remainingTime: -100);
        vm.RemainingTime.Should().Be("00:00:00");
    }

    // ==================== VIEW MESSAGES COMMAND ====================

    [Fact]
    public void ViewMessagesCommand_WithUnreadMessages_ShouldFireEvent()
    {
        var (vm, _) = CreateVm();
        vm.UnreadMessages = 3;

        bool fired = false;
        vm.ViewMessagesRequested += () => fired = true;

        vm.ViewMessagesCommand.Execute(null);
        fired.Should().BeTrue();
    }

    [Fact]
    public void ViewMessagesCommand_WithNoMessages_ShouldNotFireEvent()
    {
        var (vm, _) = CreateVm();
        vm.UnreadMessages = 0;

        bool fired = false;
        vm.ViewMessagesRequested += () => fired = true;

        vm.ViewMessagesCommand.Execute(null);
        fired.Should().BeFalse();
    }

    // ==================== IS SESSION INACTIVE ====================

    [Fact]
    public void IsSessionInactive_WhenActive_ShouldBeFalse()
    {
        var (vm, _) = CreateVm();
        vm.IsSessionActive = true;
        vm.IsSessionInactive.Should().BeFalse();
    }

    [Fact]
    public void IsSessionInactive_WhenInactive_ShouldBeTrue()
    {
        var (vm, _) = CreateVm();
        vm.IsSessionActive = false;
        vm.IsSessionInactive.Should().BeTrue();
    }

    // ==================== PROPERTY CHANGED ====================

    [Fact]
    public void SettingErrorMessage_ShouldNotifyPropertyChanged()
    {
        var (vm, _) = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.ErrorMessage = "test error";
        changed.Should().Contain("ErrorMessage");
    }

    [Fact]
    public void SettingIsLoading_ShouldNotifyPropertyChanged()
    {
        var (vm, _) = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.IsLoading = true;
        changed.Should().Contain("IsLoading");
    }

    [Fact]
    public void SettingRemainingTime_ShouldNotifyPropertyChanged()
    {
        var (vm, _) = CreateVm();
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.RemainingTime = "02:00:00";
        changed.Should().Contain("RemainingTime");
    }

    // ==================== DISPOSE ====================

    [Fact]
    public void Dispose_ShouldNotThrow()
    {
        var (vm, _) = CreateVm();
        var act = () => vm.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_CalledTwice_ShouldNotThrow()
    {
        var (vm, _) = CreateVm();
        vm.Dispose();
        var act = () => vm.Dispose();
        act.Should().NotThrow();
    }

    // ==================== START/END SESSION COMMANDS ====================

    [Fact]
    public async Task StartSessionCommand_WithZeroRemainingTime_ShouldSetError()
    {
        var (vm, _) = CreateVm(remainingTime: 0);
        _handler.WhenRaw("users/user-123.json", "{\"remainingTime\": 0}");

        // Use the operating hours metadata mock
        _handler.WhenRaw("metadata.json", "{\"operatingHours\":{\"enabled\":false}}");

        await vm.StartSessionCommand.ExecuteAsync(null);

        vm.ErrorMessage.Should().NotBeNullOrEmpty();
        vm.IsSessionActive.Should().BeFalse();
    }

    [Fact]
    public async Task EndSessionCommand_WhenNotActive_ShouldNoOp()
    {
        var (vm, _) = CreateVm();
        vm.IsSessionActive.Should().BeFalse();

        await vm.EndSessionCommand.ExecuteAsync(null);
        // No crash, no state change
        vm.IsSessionActive.Should().BeFalse();
    }
}
