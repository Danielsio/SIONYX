using FluentAssertions;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class AuthViewModelTests
{
    private readonly AuthViewModel _vm;

    public AuthViewModelTests()
    {
        var authService = new AuthService(null!, null!, null!);
        _vm = new AuthViewModel(authService);
    }

    [Fact]
    public void InitialState_ShouldBeLoginMode()
    {
        _vm.IsLoginMode.Should().BeTrue();
        _vm.IsLoading.Should().BeFalse();
        _vm.ErrorMessage.Should().BeEmpty();
        _vm.Phone.Should().BeEmpty();
        _vm.Password.Should().BeEmpty();
    }

    [Fact]
    public void ToggleMode_ShouldSwitchBetweenLoginAndRegister()
    {
        _vm.IsLoginMode.Should().BeTrue();
        _vm.ToggleModeCommand.Execute(null);
        _vm.IsLoginMode.Should().BeFalse();
        _vm.ToggleModeCommand.Execute(null);
        _vm.IsLoginMode.Should().BeTrue();
    }

    [Fact]
    public void ToggleMode_ShouldClearErrorMessage()
    {
        _vm.ErrorMessage = "Some error";
        _vm.ToggleModeCommand.Execute(null);
        _vm.ErrorMessage.Should().BeEmpty();
    }

    [Fact]
    public async Task Login_WithEmptyFields_ShouldSetError()
    {
        _vm.Phone = "";
        _vm.Password = "";
        await _vm.LoginCommand.ExecuteAsync(null);
        _vm.ErrorMessage.Should().NotBeEmpty();
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task Login_WithMissingPassword_ShouldSetError()
    {
        _vm.Phone = "0501234567";
        _vm.Password = "";
        await _vm.LoginCommand.ExecuteAsync(null);
        _vm.ErrorMessage.Should().NotBeEmpty();
    }

    [Fact]
    public async Task Register_WithMissingFields_ShouldSetError()
    {
        _vm.IsLoginMode = false;
        _vm.Phone = "0501234567";
        _vm.Password = "password";
        _vm.FirstName = "";
        _vm.LastName = "";
        await _vm.RegisterCommand.ExecuteAsync(null);
        _vm.ErrorMessage.Should().NotBeEmpty();
    }

    [Fact]
    public void TriggerAutoLogin_ShouldRaiseEvent()
    {
        var raised = false;
        _vm.LoginSucceeded += () => raised = true;
        _vm.TriggerAutoLogin();
        raised.Should().BeTrue();
    }

    [Fact]
    public void PropertyChanged_ShouldFireForPhone()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);
        _vm.Phone = "0501234567";
        changed.Should().Contain("Phone");
    }
}
