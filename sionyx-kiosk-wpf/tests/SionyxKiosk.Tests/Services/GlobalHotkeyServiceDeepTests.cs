using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Deep tests for GlobalHotkeyService covering ParseHotkey and ResolveAdminExitHotkey.
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

    [Theory]
    [InlineData("ctrl+alt+space", 0x0003u, 0x20u)]     // Ctrl(2) + Alt(1) = 3, Space = 0x20
    [InlineData("ctrl+alt+q", 0x0003u, 0x51u)]          // Ctrl + Alt = 3, Q = 0x51
    [InlineData("ctrl+shift+space", 0x0006u, 0x20u)]    // Ctrl(2) + Shift(4) = 6
    [InlineData("alt+shift+q", 0x0005u, 0x51u)]         // Alt(1) + Shift(4) = 5
    [InlineData("ctrl+alt+shift+q", 0x0007u, 0x51u)]    // Ctrl + Alt + Shift = 7
    [InlineData("ctrl+a", 0x0002u, 65u)]                // Ctrl(2), A = 65
    public void ParseHotkey_ShouldParseCorrectly(string hotkey, uint expectedMod, uint expectedVk)
    {
        var method = typeof(GlobalHotkeyService).GetMethod("ParseHotkey",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var result = ((uint modifiers, uint vk))method.Invoke(null, new object[] { hotkey })!;
        result.modifiers.Should().Be(expectedMod);
        result.vk.Should().Be(expectedVk);
    }

    [Fact]
    public void ParseHotkey_WithSpaces_ShouldStillParse()
    {
        var method = typeof(GlobalHotkeyService).GetMethod("ParseHotkey",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var result = ((uint, uint))method.Invoke(null, new object[] { " ctrl + alt + space " })!;
        result.Item1.Should().BeGreaterThan(0u);
    }

    [Fact]
    public void ParseHotkey_DefaultOnlySpace_ShouldReturnSpaceVk()
    {
        var method = typeof(GlobalHotkeyService).GetMethod("ParseHotkey",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var result = ((uint, uint))method.Invoke(null, new object[] { "space" })!;
        result.Item2.Should().Be(0x20u); // VK_SPACE
    }

    [Fact]
    public void AdminExitRequested_ShouldBeSubscribable()
    {
        _service.AdminExitRequested += () => { };
        _service.Should().NotBeNull();
    }
}
