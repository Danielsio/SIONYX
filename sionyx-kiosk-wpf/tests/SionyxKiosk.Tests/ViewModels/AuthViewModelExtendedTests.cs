using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class AuthViewModelExtendedTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly LocalDatabase _localDb;
    private readonly AuthViewModel _vm;
    private readonly string _dbPath;

    public AuthViewModelExtendedTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _dbPath = Path.Combine(Path.GetTempPath(), $"auth_vm_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
        var authService = new AuthService(_firebase, _localDb);
        _vm = new AuthViewModel(authService);
    }

    public void Dispose()
    {
        _firebase.Dispose();
        _localDb.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    [Fact]
    public async Task LoginCommand_WithValidCredentials_ShouldSucceed()
    {
        _handler.When("signInWithPassword", new
        {
            idToken = "token",
            refreshToken = "refresh",
            localId = "user-123",
            expiresIn = "3600"
        });
        _handler.When("users/user-123.json", new
        {
            firstName = "David",
            lastName = "Cohen",
            phoneNumber = "0501234567",
            isLoggedIn = false,
        });
        _handler.SetDefaultSuccess();

        var loginSucceeded = false;
        _vm.LoginSucceeded += () => loginSucceeded = true;

        _vm.Phone = "0501234567";
        _vm.Password = "password123";
        await _vm.LoginCommand.ExecuteAsync(null);

        loginSucceeded.Should().BeTrue();
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task LoginCommand_WhenFails_ShouldSetError()
    {
        _handler.WhenError("signInWithPassword", System.Net.HttpStatusCode.BadRequest);

        _vm.Phone = "0501234567";
        _vm.Password = "wrong_password";
        await _vm.LoginCommand.ExecuteAsync(null);

        _vm.ErrorMessage.Should().NotBeEmpty();
        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterCommand_WithValidData_ShouldCompleteWithoutError()
    {
        _handler.When("signUp", new
        {
            idToken = "token",
            refreshToken = "refresh",
            localId = "user-456",
            expiresIn = "3600"
        });
        _handler.SetDefaultSuccess();

        _vm.IsLoginMode = false;
        _vm.Phone = "0501234567";
        _vm.Password = "password123";
        _vm.FirstName = "David";
        _vm.LastName = "Cohen";
        await _vm.RegisterCommand.ExecuteAsync(null);

        _vm.IsLoading.Should().BeFalse();
    }

    [Fact]
    public async Task RegisterCommand_WhenFails_ShouldSetError()
    {
        _handler.WhenError("signUp", System.Net.HttpStatusCode.BadRequest);

        _vm.IsLoginMode = false;
        _vm.Phone = "0501234567";
        _vm.Password = "password123";
        _vm.FirstName = "David";
        _vm.LastName = "Cohen";
        await _vm.RegisterCommand.ExecuteAsync(null);

        _vm.ErrorMessage.Should().NotBeEmpty();
    }

    [Fact]
    public void PropertyChanged_ShouldFireForAllProperties()
    {
        var changed = new List<string>();
        _vm.PropertyChanged += (_, e) => changed.Add(e.PropertyName!);

        _vm.Phone = "0501234567";
        _vm.Password = "pass";
        _vm.FirstName = "David";
        _vm.LastName = "Cohen";
        _vm.IsLoginMode = false;
        _vm.IsLoading = true;
        _vm.ErrorMessage = "error";

        changed.Should().Contain("Phone");
        changed.Should().Contain("Password");
        changed.Should().Contain("FirstName");
        changed.Should().Contain("LastName");
        changed.Should().Contain("IsLoginMode");
        changed.Should().Contain("IsLoading");
        changed.Should().Contain("ErrorMessage");
    }

    [Fact]
    public async Task LoginCommand_WithMissingPhone_ShouldSetError()
    {
        _vm.Phone = "";
        _vm.Password = "password123";
        await _vm.LoginCommand.ExecuteAsync(null);
        _vm.ErrorMessage.Should().NotBeEmpty();
    }

    [Fact]
    public void ToggleMode_ShouldResetFields()
    {
        _vm.ErrorMessage = "Some error";
        _vm.ToggleModeCommand.Execute(null);
        _vm.ErrorMessage.Should().BeEmpty();
    }
}
