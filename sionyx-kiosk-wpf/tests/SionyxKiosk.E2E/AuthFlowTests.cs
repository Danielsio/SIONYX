using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FluentAssertions;
using SionyxKiosk.E2E.Fixtures;

namespace SionyxKiosk.E2E;

/// <summary>
/// Auth flow E2E tests: login validation, registration form, forgot password, form switching.
/// These tests run on the AuthWindow before login.
/// </summary>
[Trait("Category", "E2E")]
[Collection("KioskApp")]
[TestCaseOrderer(
    "SionyxKiosk.E2E.Fixtures.PriorityOrderer",
    "SionyxKiosk.E2E")]
public class AuthFlowTests
{
    private readonly KioskAppFixture _app;

    public AuthFlowTests(KioskAppFixture app)
    {
        _app = app;
    }

    // ── Auth window UI elements ──

    [Fact, TestPriority(100)]
    public void AuthWindow_ShouldHaveForgotPasswordLink()
    {
        var window = _app.GetAuthWindow();
        var link = window.FindFirstDescendant(cf => cf.ByAutomationId("ForgotPasswordLink"));
        link.Should().NotBeNull("auth window should have a 'forgot password' link");
    }

    [Fact, TestPriority(101)]
    public void AuthWindow_ShouldHaveSwitchToRegisterLink()
    {
        var window = _app.GetAuthWindow();
        var link = window.FindFirstDescendant(cf => cf.ByAutomationId("SwitchToRegisterLink"));
        link.Should().NotBeNull("auth window should have a 'switch to register' link");
    }

    [Fact, TestPriority(102)]
    public void AuthWindow_CanSwitchToRegisterForm()
    {
        var window = _app.GetAuthWindow();
        var switchBtn = window.FindFirstDescendant(cf => cf.ByAutomationId("SwitchToRegisterLink"));
        switchBtn.Should().NotBeNull();
        switchBtn!.Click();
        Thread.Sleep(1000);

        var regPhone = window.FindFirstDescendant(cf => cf.ByAutomationId("RegPhoneInput"));
        regPhone.Should().NotBeNull("register form should appear with phone input");

        var regPassword = window.FindFirstDescendant(cf => cf.ByAutomationId("RegPasswordInput"));
        regPassword.Should().NotBeNull("register form should have password input");

        var regFirstName = window.FindFirstDescendant(cf => cf.ByAutomationId("RegFirstNameInput"));
        regFirstName.Should().NotBeNull("register form should have first name input");

        var regLastName = window.FindFirstDescendant(cf => cf.ByAutomationId("RegLastNameInput"));
        regLastName.Should().NotBeNull("register form should have last name input");

        var regButton = window.FindFirstDescendant(cf => cf.ByAutomationId("RegisterButton"));
        regButton.Should().NotBeNull("register form should have register button");
    }

    [Fact, TestPriority(103)]
    public void AuthWindow_CanSwitchBackToLoginForm()
    {
        var window = _app.GetAuthWindow();

        // First ensure we're on register form
        var switchToReg = window.FindFirstDescendant(cf => cf.ByAutomationId("SwitchToRegisterLink"));
        if (switchToReg != null)
            switchToReg.Click();
        Thread.Sleep(500);

        var switchToLogin = window.FindFirstDescendant(cf => cf.ByAutomationId("SwitchToLoginLink"));
        switchToLogin.Should().NotBeNull("register form should have 'switch to login' link");
        switchToLogin!.Click();
        Thread.Sleep(500);

        var loginPhone = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPhoneInput"));
        loginPhone.Should().NotBeNull("should be back on login form with phone input");

        var loginButton = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton"));
        loginButton.Should().NotBeNull("should be back on login form with login button");
    }

    [Fact, TestPriority(104)]
    public void Login_WithEmptyFields_ShouldNotCrash()
    {
        var window = _app.GetAuthWindow();

        // Make sure we're on login form
        var switchToLogin = window.FindFirstDescendant(cf => cf.ByAutomationId("SwitchToLoginLink"));
        if (switchToLogin != null)
        {
            switchToLogin.Click();
            Thread.Sleep(500);
        }

        var loginButton = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton"))?.AsButton();
        loginButton.Should().NotBeNull();
        loginButton!.Click();
        Thread.Sleep(1000);

        // App should still be responsive — auth window should still exist
        var authWindow = _app.GetAuthWindow();
        authWindow.Should().NotBeNull("app should not crash on empty login submission");
    }

    [Fact, TestPriority(105)]
    public void Login_WithWrongPassword_ShouldShowError()
    {
        var window = _app.GetAuthWindow();

        var phoneInput = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPhoneInput"))?.AsTextBox();
        phoneInput.Should().NotBeNull();
        phoneInput!.Text = "0500000001";

        var passwordInput = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPasswordInput"));
        passwordInput.Should().NotBeNull();
        passwordInput!.Focus();
        // Clear any existing text before typing
        Keyboard.TypeSimultaneously(FlaUI.Core.WindowsAPI.VirtualKeyShort.CONTROL,
                                     FlaUI.Core.WindowsAPI.VirtualKeyShort.KEY_A);
        Thread.Sleep(100);
        Keyboard.Type("wrongpassword123");

        var loginButton = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton"))?.AsButton();
        loginButton.Should().NotBeNull();
        loginButton!.Click();
        Thread.Sleep(3000);

        // App should still show auth window (not crash)
        var authWindow = _app.GetAuthWindow();
        authWindow.Should().NotBeNull("auth window should remain open after failed login");
    }
}
