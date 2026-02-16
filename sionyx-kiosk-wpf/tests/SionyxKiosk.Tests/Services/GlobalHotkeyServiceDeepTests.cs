using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Tests for GlobalHotkeyService (low-level keyboard hook approach).
/// </summary>
public class GlobalHotkeyServiceDeepTests : IDisposable
{
    private readonly GlobalHotkeyService _service;

    public GlobalHotkeyServiceDeepTests()
    {
        _service = new GlobalHotkeyService();
    }

    public void Dispose() => _service.Dispose();

    [Fact]
    public void AdminExitHotkey_ShouldHaveValue()
    {
        _service.AdminExitHotkey.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void IsRunning_Initially_ShouldBeFalse()
    {
        _service.IsRunning.Should().BeFalse();
    }

    [Fact]
    public void Stop_WhenNotRunning_ShouldNotThrow()
    {
        var act = () => _service.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_MultipleTimes_ShouldNotThrow()
    {
        _service.Dispose();
        var act = () => _service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void AdminExitRequested_ShouldBeSubscribable()
    {
        _service.AdminExitRequested += () => { };
        _service.Should().NotBeNull();
    }

    [Fact]
    public void Start_WithOverload_ShouldAcceptIntPtr()
    {
        // The Start(IntPtr) overload is kept for backward compatibility.
        // It should delegate to Start() without errors.
        // (We can't fully test the hook without a message loop, but we
        //  verify it doesn't throw.)
        var act = () => _service.Start(IntPtr.Zero);
        act.Should().NotThrow();
    }
}
