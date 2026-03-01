using FluentAssertions;
using SionyxKiosk.E2E.Fixtures;

namespace SionyxKiosk.E2E;

[Trait("Category", "E2E")]
public class SmokeTests : IClassFixture<KioskAppFixture>
{
    private readonly KioskAppFixture _app;

    public SmokeTests(KioskAppFixture app)
    {
        _app = app;
    }

    [Fact]
    public void AuthWindow_ShouldAppear()
    {
        var window = _app.GetAuthWindow();
        window.Should().NotBeNull();
        window.Title.Should().Contain("SIONYX");
    }

    [Fact]
    public void AuthWindow_ShouldHavePhoneInput()
    {
        var window = _app.GetAuthWindow();
        var input = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPhoneInput"));
        input.Should().NotBeNull("auth window should contain the phone input field");
    }

    [Fact]
    public void AuthWindow_ShouldHavePasswordInput()
    {
        var window = _app.GetAuthWindow();
        var input = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginPasswordInput"));
        input.Should().NotBeNull("auth window should contain the password input field");
    }

    [Fact]
    public void AuthWindow_ShouldHaveLoginButton()
    {
        var window = _app.GetAuthWindow();
        var button = window.FindFirstDescendant(cf => cf.ByAutomationId("LoginButton"));
        button.Should().NotBeNull("auth window should contain the login button");
    }
}
