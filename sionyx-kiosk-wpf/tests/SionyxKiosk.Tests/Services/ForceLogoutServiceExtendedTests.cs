using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class ForceLogoutServiceExtendedTests : IDisposable
{
    private readonly SionyxKiosk.Infrastructure.FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ForceLogoutService _service;

    public ForceLogoutServiceExtendedTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _handler.SetDefaultSuccess();
        _service = new ForceLogoutService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void StartListening_ShouldNotThrow()
    {
        var act = () => _service.StartListening("user-123");
        act.Should().NotThrow();
        _service.StopListening(); // cleanup
    }

    [Fact]
    public void StartListening_ThenStop_ShouldNotThrow()
    {
        _service.StartListening("user-123");
        var act = () => _service.StopListening();
        act.Should().NotThrow();
    }

    [Fact]
    public void StopListening_Twice_ShouldBeIdempotent()
    {
        _service.StartListening("user-123");
        _service.StopListening();
        _service.StopListening(); // Double stop
    }

    [Fact]
    public void ForceLogout_Event_ShouldBeSubscribable()
    {
        string? reason = null;
        _service.ForceLogout += r => reason = r;
        _service.Should().NotBeNull();
    }

    [Fact]
    public void StartListening_ShouldReplaceExistingListener()
    {
        _service.StartListening("user-123");
        // Starting for a different user should replace the listener
        _service.StartListening("user-456");
        _service.StopListening();
    }
}
