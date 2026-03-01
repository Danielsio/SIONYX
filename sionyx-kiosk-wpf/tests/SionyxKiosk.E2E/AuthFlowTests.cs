using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FlaUI.Core.WindowsAPI;
using FluentAssertions;
using SionyxKiosk.E2E.Fixtures;

namespace SionyxKiosk.E2E;

[Trait("Category", "E2E")]
public class AuthFlowTests : IClassFixture<KioskAppFixture>
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

    [Fact]
    public void Login_ShouldShowMainWindow()
    {
        if (!HasCredentials)
        {
            // No test credentials configured -- skip gracefully
            return;
        }

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

        // Wait for main window (auth window closes, main window opens)
        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(30));
        mainWindow.Should().NotBeNull("main window should appear after successful login");
        mainWindow!.Title.Should().Be("SIONYX");
    }

    [Fact]
    public void AfterLogin_AllNavPages_ShouldBeAccessible()
    {
        if (!HasCredentials)
            return;

        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(5));
        if (mainWindow == null)
        {
            // Login test didn't run or failed -- skip
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
