using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class MainViewModelTests
{
    private readonly MainViewModel _vm;

    public MainViewModelTests()
    {
        var authService = new AuthService(null!, null!);
        _vm = new MainViewModel(authService);
    }

    [Fact]
    public void InitialState_ShouldBeHomePage()
    {
        _vm.CurrentPage.Should().Be("Home");
        _vm.IsSidebarCollapsed.Should().BeFalse();
    }

    [Fact]
    public void Navigate_ShouldChangeCurrentPage()
    {
        _vm.NavigateCommand.Execute("Packages");
        _vm.CurrentPage.Should().Be("Packages");
        _vm.NavigateCommand.Execute("History");
        _vm.CurrentPage.Should().Be("History");
        _vm.NavigateCommand.Execute("Help");
        _vm.CurrentPage.Should().Be("Help");
    }

    [Fact]
    public void ToggleSidebar_ShouldFlipCollapsedState()
    {
        _vm.IsSidebarCollapsed.Should().BeFalse();
        _vm.ToggleSidebarCommand.Execute(null);
        _vm.IsSidebarCollapsed.Should().BeTrue();
        _vm.ToggleSidebarCommand.Execute(null);
        _vm.IsSidebarCollapsed.Should().BeFalse();
    }

    [Fact]
    public void Navigate_ShouldRaisePropertyChanged()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);
        _vm.NavigateCommand.Execute("Packages");
        changed.Should().Contain("CurrentPage");
    }

    [Fact(Skip = "LogoutCommand calls AuthService.LogoutAsync which uses LocalDatabase/Firebase; null deps cause NRE before event. Requires integration test with real deps.")]
    public async Task Logout_ShouldRaiseLogoutRequestedEvent()
    {
        var raised = false;
        _vm.LogoutRequested += () => raised = true;
        await _vm.LogoutCommand.ExecuteAsync(null);
        raised.Should().BeTrue();
    }
}
