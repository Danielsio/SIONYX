using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class MainViewModelExtendedTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly LocalDatabase _localDb;
    private readonly string _dbPath;

    public MainViewModelExtendedTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _dbPath = Path.Combine(Path.GetTempPath(), $"main_vm_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
        _handler.SetDefaultSuccess();
    }

    public void Dispose()
    {
        _firebase.Dispose();
        _localDb.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    [Fact]
    public void LogoutCommand_ShouldRaiseLogoutRequestedEvent()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new MainViewModel(auth);

        var raised = false;
        vm.LogoutRequested += () => raised = true;

        vm.LogoutCommand.Execute(null);

        raised.Should().BeTrue();
    }

    [Fact]
    public void CurrentUser_ShouldReflectAuthServiceUser()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new MainViewModel(auth);
        // Auth has no current user by default
        vm.CurrentUser.Should().BeNull();
    }

    [Fact]
    public void Navigate_ToAllPages_ShouldWork()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new MainViewModel(auth);

        foreach (var page in new[] { "Home", "Packages", "History", "Help", "Messages" })
        {
            vm.NavigateCommand.Execute(page);
            vm.CurrentPage.Should().Be(page);
        }
    }

    [Fact]
    public void ToggleSidebar_MultipleTimes_ShouldAlternate()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new MainViewModel(auth);

        for (int i = 0; i < 5; i++)
        {
            vm.ToggleSidebarCommand.Execute(null);
            var expected = i % 2 == 0; // 1st toggle=True, 2nd=False, 3rd=True...
            vm.IsSidebarCollapsed.Should().Be(expected);
        }
    }

    [Fact]
    public void PropertyChanged_ShouldFireForCurrentUser()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new MainViewModel(auth);
        var changed = new List<string>();
        vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        vm.CurrentUser = new UserData { FirstName = "Test" };

        changed.Should().Contain("CurrentUser");
    }
}
