using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FluentAssertions;
using SionyxKiosk.E2E.Fixtures;

namespace SionyxKiosk.E2E;

[Trait("Category", "E2E")]
[Collection("KioskApp")]
[TestCaseOrderer(
    "SionyxKiosk.E2E.Fixtures.PriorityOrderer",
    "SionyxKiosk.E2E")]
public class KioskE2ETests
{
    private readonly KioskAppFixture _app;
    private readonly string? _phone;
    private readonly string? _password;

    public KioskE2ETests(KioskAppFixture app)
    {
        _app = app;
        _phone = Environment.GetEnvironmentVariable("SIONYX_E2E_PHONE");
        _password = Environment.GetEnvironmentVariable("SIONYX_E2E_PASSWORD");
    }

    private bool HasCredentials => !string.IsNullOrEmpty(_phone) && !string.IsNullOrEmpty(_password);

    // ── Smoke tests (run first, before login) ──

    [Fact, TestPriority(1)]
    public void AuthWindow_ShouldAppear()
    {
        var window = _app.GetAuthWindow();
        window.Should().NotBeNull();
        window.Title.Should().Contain("SIONYX");
    }

    [Fact, TestPriority(2)]
    public void AuthWindow_ShouldHavePhoneInput()
    {
        var window = _app.GetAuthWindow();
        var input = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPhoneInput"));
        input.Should().NotBeNull("auth window should contain the phone input field");
    }

    [Fact, TestPriority(3)]
    public void AuthWindow_ShouldHavePasswordInput()
    {
        var window = _app.GetAuthWindow();
        var input = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPasswordInput"));
        input.Should().NotBeNull("auth window should contain the password input field");
    }

    [Fact, TestPriority(4)]
    public void AuthWindow_ShouldHaveLoginButton()
    {
        var window = _app.GetAuthWindow();
        var button = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton"));
        button.Should().NotBeNull("auth window should contain the login button");
    }

    // ── Auth flow tests (run after smoke tests) ──

    [Fact, TestPriority(10)]
    public void Login_ShouldShowMainWindow()
    {
        if (!HasCredentials)
            return;

        var authWindow = _app.GetAuthWindow();

        var phoneInput = authWindow.FindFirstDescendant(cf => cf.ByAutomationId("LoginPhoneInput"))?.AsTextBox();
        phoneInput.Should().NotBeNull();
        phoneInput!.Text = _phone!;

        var passwordInput = authWindow.FindFirstDescendant(cf => cf.ByAutomationId("LoginPasswordInput"));
        passwordInput.Should().NotBeNull();
        passwordInput!.Focus();
        Keyboard.Type(_password!);

        var loginButton = authWindow.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton"))?.AsButton();
        loginButton.Should().NotBeNull();
        loginButton!.Click();

        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(30), exact: true);
        mainWindow.Should().NotBeNull("main window should appear after successful login");
        mainWindow!.Title.Should().Be("SIONYX");
    }

    [Fact, TestPriority(20)]
    public void AfterLogin_AllNavPages_ShouldBeAccessible()
    {
        if (!HasCredentials)
            return;

        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(10), exact: true);
        mainWindow.Should().NotBeNull("should be logged in from Login_ShouldShowMainWindow");

        var navIds = new[] { "NavPackages", "NavHistory", "NavPrintHistory", "NavHelp", "NavHome" };

        foreach (var navId in navIds)
        {
            var navButton = mainWindow!.FindFirstDescendant(cf => cf.ByAutomationId(navId));
            navButton.Should().NotBeNull($"nav button '{navId}' should exist");
            navButton!.Click();
            Thread.Sleep(1000);
        }
    }
}
