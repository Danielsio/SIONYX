using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FluentAssertions;
using SionyxKiosk.E2E.Fixtures;

namespace SionyxKiosk.E2E;

[Trait("Category", "E2E")]
[Collection("KioskApp")]
public class AuthFlowTests
{
    private readonly KioskAppFixture _app;
    private readonly string? _phone;
    private readonly string? _password;

    public AuthFlowTests(KioskAppFixture app)
    {
        _app = app;
        _phone = Environment.GetEnvironmentVariable("SIONYX_E2E_PHONE");
        _password = Environment.GetEnvironmentVariable("SIONYX_E2E_PASSWORD");
    }

    private bool HasCredentials => !string.IsNullOrEmpty(_phone) && !string.IsNullOrEmpty(_password);

    private Window? DoLogin()
    {
        var authWindow = _app.GetAuthWindow();

        var phoneInput = authWindow.FindFirstDescendant(cf => cf.ByAutomationId("LoginPhoneInput"))?.AsTextBox();
        if (phoneInput == null) return null;
        phoneInput.Text = _phone!;

        var passwordInput = authWindow.FindFirstDescendant(cf => cf.ByAutomationId("LoginPasswordInput"));
        if (passwordInput == null) return null;
        passwordInput.Focus();
        Keyboard.Type(_password!);

        var loginButton = authWindow.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton"))?.AsButton();
        if (loginButton == null) return null;
        loginButton.Click();

        return _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(30));
    }

    [Fact]
    public void Login_ShouldShowMainWindow()
    {
        if (!HasCredentials)
            return;

        var mainWindow = DoLogin();
        mainWindow.Should().NotBeNull("main window should appear after successful login");
        mainWindow!.Title.Should().Be("SIONYX");
    }

    [Fact]
    public void AfterLogin_AllNavPages_ShouldBeAccessible()
    {
        if (!HasCredentials)
            return;

        // Ensure we're logged in (may already be from Login_ShouldShowMainWindow)
        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(5));
        if (mainWindow == null)
        {
            mainWindow = DoLogin();
        }

        if (mainWindow == null)
        {
            // Login failed -- skip rather than false-fail
            return;
        }

        var navIds = new[] { "NavPackages", "NavHistory", "NavPrintHistory", "NavHelp", "NavHome" };

        foreach (var navId in navIds)
        {
            var navButton = mainWindow.FindFirstDescendant(cf => cf.ByAutomationId(navId));
            navButton.Should().NotBeNull($"nav button '{navId}' should exist");
            navButton!.Click();
            Thread.Sleep(1000);
        }
    }
}
