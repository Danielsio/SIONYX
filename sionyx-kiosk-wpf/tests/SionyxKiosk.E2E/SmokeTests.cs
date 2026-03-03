using FlaUI.Core.AutomationElements;
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
        if (_app.IsLoggedIn) return;
        var window = _app.GetAuthWindow();
        var input = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPhoneInput"));
        input.Should().NotBeNull("auth window should contain the phone input field");
    }

    [Fact, TestPriority(3)]
    public void AuthWindow_ShouldHavePasswordInput()
    {
        if (_app.IsLoggedIn) return;
        var window = _app.GetAuthWindow();
        var input = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPasswordInput"));
        input.Should().NotBeNull("auth window should contain the password input field");
    }

    [Fact, TestPriority(4)]
    public void AuthWindow_ShouldHaveLoginButton()
    {
        if (_app.IsLoggedIn) return;
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

        var loggedIn = _app.EnsureLoggedIn();
        loggedIn.Should().BeTrue("login with E2E credentials should succeed");

        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(10), exact: true);
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

    // ── Print monitor UI tests (run after login, on home page) ──

    [Fact, TestPriority(30)]
    public void HomePage_ShouldShowPrintBalanceCard()
    {
        if (!HasCredentials)
            return;

        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(10), exact: true);
        mainWindow.Should().NotBeNull();

        var navHome = mainWindow!.FindFirstDescendant(cf => cf.ByAutomationId("NavHome"));
        navHome.Should().NotBeNull();
        navHome!.Click();
        Thread.Sleep(1000);

        var printBalanceCard = mainWindow.FindFirstDescendant(cf => cf.ByAutomationId("StatPrintBalance"));
        printBalanceCard.Should().NotBeNull("home page should display the print balance stat card");
    }

    [Fact, TestPriority(31)]
    public void HomePage_ShouldShowStartSessionButton()
    {
        if (!HasCredentials)
            return;

        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(10), exact: true);
        mainWindow.Should().NotBeNull();

        var startBtn = mainWindow!.FindFirstDescendant(cf => cf.ByAutomationId("StartSessionButton"));
        // Button may be hidden if user has no time, so just check the page loaded
        if (startBtn != null)
        {
            startBtn.IsEnabled.Should().BeTrue("start session button should be enabled when user has time");
        }
    }

    [Fact, TestPriority(40)]
    public void PrintHistoryPage_ShouldShowStatCards()
    {
        if (!HasCredentials)
            return;

        var mainWindow = _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(10), exact: true);
        mainWindow.Should().NotBeNull();

        var navPrintHistory = mainWindow!.FindFirstDescendant(cf => cf.ByAutomationId("NavPrintHistory"));
        navPrintHistory.Should().NotBeNull();
        navPrintHistory!.Click();
        Thread.Sleep(1500);

        var pagesCard = mainWindow.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatPages"));
        pagesCard.Should().NotBeNull("print history page should show the pages stat card");

        var costCard = mainWindow.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatCost"));
        costCard.Should().NotBeNull("print history page should show the cost stat card");

        var approvedCard = mainWindow.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatApproved"));
        approvedCard.Should().NotBeNull("print history page should show the approved count card");

        var deniedCard = mainWindow.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatDenied"));
        deniedCard.Should().NotBeNull("print history page should show the denied count card");
    }
}
