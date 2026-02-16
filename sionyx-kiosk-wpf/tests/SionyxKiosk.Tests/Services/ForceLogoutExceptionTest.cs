using System.Reflection;
using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Test that triggers the exception catch block in ForceLogoutService.OnEvent
/// by having the event handler throw.
/// </summary>
public class ForceLogoutExceptionTest : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly ForceLogoutService _service;

    public ForceLogoutExceptionTest()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new ForceLogoutService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    [Fact]
    public void OnEvent_WhenHandlerThrows_ShouldCatchException()
    {
        // Register a handler that throws - this should be caught by the try/catch in OnEvent
        _service.ForceLogout += _ => throw new InvalidOperationException("Handler crashed");

        _handler.SetDefaultSuccess();
        _service.StartListening("test-user");
        _service.StopListening();

        var method = typeof(ForceLogoutService).GetMethod("OnEvent",
            BindingFlags.NonPublic | BindingFlags.Instance)!;

        var data = TestFirebaseFactory.ToJsonElement(new { reason = "test" });

        // This should NOT throw - the catch block should handle it
        var act = () => method.Invoke(_service, new object?[] { "put", (JsonElement?)data });
        // The TargetInvocationException wraps the actual exception, but OnEvent catches it internally
        // So this should not propagate
        act.Should().NotThrow();
    }
}
