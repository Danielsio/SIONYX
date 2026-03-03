using FlaUI.Core.AutomationElements;
using FluentAssertions;
using SionyxKiosk.E2E.Fixtures;

namespace SionyxKiosk.E2E;

/// <summary>
/// Navigation E2E tests: verify each page loads correctly with expected UI elements.
/// Requires valid login credentials (SIONYX_E2E_PHONE / SIONYX_E2E_PASSWORD).
/// </summary>
[Trait("Category", "E2E")]
[Collection("KioskApp")]
[TestCaseOrderer(
    "SionyxKiosk.E2E.Fixtures.PriorityOrderer",
    "SionyxKiosk.E2E")]
public class NavigationTests
{
    private readonly KioskAppFixture _app;

    public NavigationTests(KioskAppFixture app)
    {
        _app = app;
    }

    private bool HasCredentials =>
        !string.IsNullOrEmpty(Environment.GetEnvironmentVariable("SIONYX_E2E_PHONE")) &&
        !string.IsNullOrEmpty(Environment.GetEnvironmentVariable("SIONYX_E2E_PASSWORD"));

    private Window? GetMainWindow()
    {
        _app.EnsureLoggedIn();
        return _app.WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(10), exact: true);
    }

    // ── Home Page ──

    [Fact, TestPriority(200)]
    public void HomePage_ShouldShowAllStatCards()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var navHome = main!.FindFirstDescendant(cf => cf.ByAutomationId("NavHome"));
        navHome!.Click();
        Thread.Sleep(1500);

        var timeCard = main.FindFirstDescendant(cf => cf.ByAutomationId("StatTimeRemaining"));
        timeCard.Should().NotBeNull("home page should show time remaining stat card");

        var printCard = main.FindFirstDescendant(cf => cf.ByAutomationId("StatPrintBalance"));
        printCard.Should().NotBeNull("home page should show print balance stat card");

        var expiryCard = main.FindFirstDescendant(cf => cf.ByAutomationId("StatExpiry"));
        expiryCard.Should().NotBeNull("home page should show expiry stat card");

        var messagesCard = main.FindFirstDescendant(cf => cf.ByAutomationId("StatMessages"));
        messagesCard.Should().NotBeNull("home page should show messages stat card");
    }

    [Fact, TestPriority(201)]
    public void HomePage_ShouldShowBuyOrStartButton()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        // Either StartSession or BuyPackage should be visible
        var startBtn = main!.FindFirstDescendant(cf => cf.ByAutomationId("StartSessionButton"));
        var buyBtn = main.FindFirstDescendant(cf => cf.ByAutomationId("BuyPackageButton"));
        (startBtn != null || buyBtn != null).Should().BeTrue(
            "home page should show either 'Start Session' or 'Buy Package' button");
    }

    // ── Packages Page ──

    [Fact, TestPriority(210)]
    public void PackagesPage_ShouldLoadWithHeader()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var navPackages = main!.FindFirstDescendant(cf => cf.ByAutomationId("NavPackages"));
        navPackages.Should().NotBeNull();
        navPackages!.Click();
        Thread.Sleep(1500);

        var header = main.FindFirstDescendant(cf => cf.ByAutomationId("PackagesPageHeader"));
        header.Should().NotBeNull("packages page should have a page header");
    }

    [Fact, TestPriority(211)]
    public void PackagesPage_ShouldShowPackagesList()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var navPackages = main!.FindFirstDescendant(cf => cf.ByAutomationId("NavPackages"));
        navPackages!.Click();
        Thread.Sleep(1500);

        var list = main.FindFirstDescendant(cf => cf.ByAutomationId("PackagesList"));
        list.Should().NotBeNull("packages page should show packages list/grid");
    }

    // ── History Page ──

    [Fact, TestPriority(220)]
    public void HistoryPage_ShouldLoadWithSearchBox()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var navHistory = main!.FindFirstDescendant(cf => cf.ByAutomationId("NavHistory"));
        navHistory.Should().NotBeNull();
        navHistory!.Click();
        Thread.Sleep(1500);

        var searchBox = main.FindFirstDescendant(cf => cf.ByAutomationId("HistorySearchBox"));
        searchBox.Should().NotBeNull("history page should have a search box");
    }

    [Fact, TestPriority(221)]
    public void HistoryPage_ShouldShowPurchasesList()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var list = main!.FindFirstDescendant(cf => cf.ByAutomationId("PurchasesList"));
        list.Should().NotBeNull("history page should have purchases list");
    }

    // ── Print History Page ──

    [Fact, TestPriority(230)]
    public void PrintHistoryPage_ShouldShowAllFourStatCards()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var navPrint = main!.FindFirstDescendant(cf => cf.ByAutomationId("NavPrintHistory"));
        navPrint.Should().NotBeNull();
        navPrint!.Click();
        Thread.Sleep(1500);

        main.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatPages"))
            .Should().NotBeNull("print history should show pages stat");
        main.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatCost"))
            .Should().NotBeNull("print history should show cost stat");
        main.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatApproved"))
            .Should().NotBeNull("print history should show approved stat");
        main.FindFirstDescendant(cf => cf.ByAutomationId("PrintStatDenied"))
            .Should().NotBeNull("print history should show denied stat");
    }

    // ── Help Page ──

    [Fact, TestPriority(240)]
    public void HelpPage_ShouldShowFaqAndContact()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var navHelp = main!.FindFirstDescendant(cf => cf.ByAutomationId("NavHelp"));
        navHelp.Should().NotBeNull();
        navHelp!.Click();
        Thread.Sleep(1500);

        var faq = main.FindFirstDescendant(cf => cf.ByAutomationId("FaqSection"));
        faq.Should().NotBeNull("help page should have FAQ section");

        var contact = main.FindFirstDescendant(cf => cf.ByAutomationId("ContactSection"));
        contact.Should().NotBeNull("help page should have contact section");
    }

    // ── Navigation Consistency ──

    [Fact, TestPriority(250)]
    public void Navigation_ShouldReturnToHomePage()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        // Navigate away
        var navHelp = main!.FindFirstDescendant(cf => cf.ByAutomationId("NavHelp"));
        navHelp!.Click();
        Thread.Sleep(500);

        // Navigate back home
        var navHome = main.FindFirstDescendant(cf => cf.ByAutomationId("NavHome"));
        navHome!.Click();
        Thread.Sleep(1000);

        // Home-specific element should be present
        var timeCard = main.FindFirstDescendant(cf => cf.ByAutomationId("StatTimeRemaining"));
        timeCard.Should().NotBeNull("navigating back to Home should show time remaining card");
    }

    [Fact, TestPriority(251)]
    public void Navigation_RapidPageSwitching_ShouldNotCrash()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var navIds = new[] { "NavPackages", "NavHome", "NavHistory", "NavHelp", "NavPrintHistory", "NavHome" };
        foreach (var navId in navIds)
        {
            var nav = main!.FindFirstDescendant(cf => cf.ByAutomationId(navId));
            nav.Should().NotBeNull($"nav button '{navId}' should exist");
            nav!.Click();
            Thread.Sleep(300);
        }

        // App should still be alive
        main = GetMainWindow();
        main.Should().NotBeNull("app should survive rapid page switching");
    }

    // ── Logout ──

    [Fact, TestPriority(260)]
    public void MainWindow_ShouldHaveLogoutButton()
    {
        if (!HasCredentials) return;
        var main = GetMainWindow();
        main.Should().NotBeNull();

        var logoutBtn = main!.FindFirstDescendant(cf => cf.ByAutomationId("LogoutButton"));
        logoutBtn.Should().NotBeNull("main window should have a logout button");
    }
}
