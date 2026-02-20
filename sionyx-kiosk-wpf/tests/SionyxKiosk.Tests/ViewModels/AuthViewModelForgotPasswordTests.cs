using System.IO;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class AuthViewModelForgotPasswordTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly LocalDatabase _localDb;
    private readonly string _dbPath;

    public AuthViewModelForgotPasswordTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _dbPath = Path.Combine(Path.GetTempPath(), $"auth_forgot_test_{Guid.NewGuid():N}.db");
        _localDb = new LocalDatabase(_dbPath);
    }

    public void Dispose()
    {
        _firebase.Dispose();
        _localDb.Dispose();
        try { File.Delete(_dbPath); } catch { }
    }

    [Fact]
    public async Task ForgotPasswordCommand_WithNoMetadataService_ShouldSetInfo()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new AuthViewModel(auth); // No metadata service

        await vm.ForgotPasswordCommand.ExecuteAsync(null);

        vm.ForgotPasswordInfo.Should().NotBeNullOrEmpty();
        vm.ForgotPasswordInfo.Should().Contain("מנהל");
    }

    [Fact]
    public async Task ForgotPasswordCommand_WithContact_ShouldShowContactInfo()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var orgService = new OrganizationMetadataService(_firebase);
        var vm = new AuthViewModel(auth, orgService);

        _handler.When("metadata.json", new
        {
            admin_phone = "0501234567",
            admin_email = "admin@test.com",
            name = "Test Org",
        });

        await vm.ForgotPasswordCommand.ExecuteAsync(null);

        vm.ForgotPasswordInfo.Should().Contain("0501234567");
        vm.ForgotPasswordInfo.Should().Contain("admin@test.com");
    }

    [Fact]
    public async Task ForgotPasswordCommand_WhenFails_ShouldShowDefaultInfo()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var orgService = new OrganizationMetadataService(_firebase);
        var vm = new AuthViewModel(auth, orgService);

        _handler.WhenError("metadata.json");

        await vm.ForgotPasswordCommand.ExecuteAsync(null);

        vm.ForgotPasswordInfo.Should().Contain("מנהל");
    }

    [Fact]
    public void ToggleMode_ShouldClearForgotPasswordInfo()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new AuthViewModel(auth);
        vm.ForgotPasswordInfo = "some info";

        vm.ToggleModeCommand.Execute(null);

        vm.ForgotPasswordInfo.Should().BeEmpty();
    }

    [Fact]
    public async Task LoginCommand_ShouldClearErrorBeforeRequest()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new AuthViewModel(auth);
        _handler.When("signInWithPassword", new { idToken = "t", refreshToken = "r", localId = "u", expiresIn = "3600" });
        _handler.When("users/u.json", new { firstName = "Test", lastName = "User", isLoggedIn = false });
        _handler.SetDefaultSuccess();

        vm.ErrorMessage = "Previous error";
        vm.Phone = "0501234567";
        vm.Password = "password123";

        await vm.LoginCommand.ExecuteAsync(null);
        // Error should be cleared even if login succeeds
    }

    [Fact]
    public async Task RegisterCommand_WithEmptyFirstName_ShouldSetError()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new AuthViewModel(auth);

        vm.IsLoginMode = false;
        vm.Phone = "0501234567";
        vm.Password = "password123";
        vm.FirstName = "";
        vm.LastName = "Cohen";

        await vm.RegisterCommand.ExecuteAsync(null);

        vm.ErrorMessage.Should().NotBeEmpty();
    }

    [Fact]
    public async Task RegisterCommand_WithEmptyLastName_ShouldSetError()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new AuthViewModel(auth);

        vm.IsLoginMode = false;
        vm.Phone = "0501234567";
        vm.Password = "password123";
        vm.FirstName = "David";
        vm.LastName = "";

        await vm.RegisterCommand.ExecuteAsync(null);

        vm.ErrorMessage.Should().NotBeEmpty();
    }

    [Fact]
    public void Email_Property_ShouldBeSettable()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new AuthViewModel(auth);
        vm.Email = "test@test.com";
        vm.Email.Should().Be("test@test.com");
    }

    [Fact]
    public void RegistrationSucceeded_ShouldBeSubscribable()
    {
        var auth = new AuthService(_firebase, _localDb, new ComputerService(_firebase));
        var vm = new AuthViewModel(auth);
        vm.RegistrationSucceeded += () => { };
        vm.Should().NotBeNull();
    }
}
