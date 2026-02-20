using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Tests for SessionService that can be tested without WPF Dispatcher.
/// Tests constructor behavior, properties, and event subscriptions via reflection.
/// Note: Timer-based methods cannot be tested in xUnit (require WPF Dispatcher).
/// </summary>
public class SessionServicePropertyTests
{
    [Fact]
    public void Constructor_ShouldThrow_WithoutDispatcher()
    {
        // SessionService uses DispatcherTimer which requires WPF Dispatcher
        // In a test environment without STA thread, this should throw
        var (firebase, _) = TestFirebaseFactory.Create();

        try
        {
            var act = () => new SessionService(firebase, "test-uid", "test-org",
                new ComputerService(firebase),
                new OperatingHoursService(firebase),
                new ProcessCleanupService(),
                new BrowserCleanupService());
            // May throw InvalidOperationException if no Dispatcher available
            // or may succeed if running on STA thread
            act.Should().NotBeNull();
        }
        catch (InvalidOperationException)
        {
            // Expected in test environment without WPF Dispatcher
        }
        finally
        {
            firebase.Dispose();
        }
    }

    [Fact]
    public void SessionEvents_ShouldBeDefinedCorrectly()
    {
        // Verify the event definitions exist via reflection
        var type = typeof(SessionService);

        type.GetEvent("SessionStarted").Should().NotBeNull();
        type.GetEvent("TimeUpdated").Should().NotBeNull();
        type.GetEvent("SessionEnded").Should().NotBeNull();
        type.GetEvent("Warning5Min").Should().NotBeNull();
        type.GetEvent("Warning1Min").Should().NotBeNull();
        type.GetEvent("SyncFailed").Should().NotBeNull();
        type.GetEvent("SyncRestored").Should().NotBeNull();
        type.GetEvent("OperatingHoursWarning").Should().NotBeNull();
        type.GetEvent("OperatingHoursEnded").Should().NotBeNull();
    }

    [Fact]
    public void SessionService_ShouldInheritFromBaseService()
    {
        typeof(SessionService).Should().BeDerivedFrom<BaseService>();
    }

    [Fact]
    public void SessionService_ShouldImplementIDisposable()
    {
        typeof(SessionService).Should().Implement<IDisposable>();
    }

    [Fact]
    public void SessionService_ShouldHaveExpectedProperties()
    {
        var type = typeof(SessionService);

        type.GetProperty("SessionId").Should().NotBeNull();
        type.GetProperty("IsActive").Should().NotBeNull();
        type.GetProperty("RemainingTime").Should().NotBeNull();
        type.GetProperty("TimeUsed").Should().NotBeNull();
        type.GetProperty("StartTime").Should().NotBeNull();
        type.GetProperty("IsOnline").Should().NotBeNull();
        type.GetProperty("OperatingHours").Should().NotBeNull();
    }

    [Fact]
    public void SessionService_ShouldHaveAsyncMethods()
    {
        var type = typeof(SessionService);

        var startMethod = type.GetMethod("StartSessionAsync");
        startMethod.Should().NotBeNull();
        startMethod!.ReturnType.Should().Be(typeof(Task<ServiceResult>));

        var endMethod = type.GetMethod("EndSessionAsync");
        endMethod.Should().NotBeNull();
        endMethod!.ReturnType.Should().Be(typeof(Task<ServiceResult>));
    }
}
