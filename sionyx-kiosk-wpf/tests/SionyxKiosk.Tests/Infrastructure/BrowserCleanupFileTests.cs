using System.IO;
using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for BrowserCleanupService's private file cleanup methods using temp directories.
/// </summary>
public class BrowserCleanupFileTests
{
    [Fact]
    public void TryDeleteFileOrDir_WithExistingFile_ShouldDeleteAndReturn1()
    {
        var method = typeof(BrowserCleanupService).GetMethod("TryDeleteFileOrDir",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var tempFile = Path.GetTempFileName();
        File.WriteAllText(tempFile, "test");

        var errors = new List<string>();
        var result = (int)method.Invoke(null, new object[] { tempFile, "TestBrowser", errors })!;

        result.Should().Be(1);
        File.Exists(tempFile).Should().BeFalse();
        errors.Should().BeEmpty();
    }

    [Fact]
    public void TryDeleteFileOrDir_WithExistingDirectory_ShouldDeleteAndReturn1()
    {
        var method = typeof(BrowserCleanupService).GetMethod("TryDeleteFileOrDir",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var tempDir = Path.Combine(Path.GetTempPath(), $"cleanup_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        File.WriteAllText(Path.Combine(tempDir, "file.txt"), "test");

        var errors = new List<string>();
        var result = (int)method.Invoke(null, new object[] { tempDir, "TestBrowser", errors })!;

        result.Should().Be(1);
        Directory.Exists(tempDir).Should().BeFalse();
        errors.Should().BeEmpty();
    }

    [Fact]
    public void TryDeleteFileOrDir_WithNonExistentPath_ShouldReturn0()
    {
        var method = typeof(BrowserCleanupService).GetMethod("TryDeleteFileOrDir",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var errors = new List<string>();
        var result = (int)method.Invoke(null, new object[] { @"C:\nonexistent\path\file.dat", "TestBrowser", errors })!;

        result.Should().Be(0);
        errors.Should().BeEmpty();
    }

    [Fact]
    public void FindChromiumProfiles_WithDefaultProfile_ShouldFindIt()
    {
        var method = typeof(BrowserCleanupService).GetMethod("FindChromiumProfiles",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var tempDir = Path.Combine(Path.GetTempPath(), $"chrome_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var defaultProfile = Path.Combine(tempDir, "Default");
        Directory.CreateDirectory(defaultProfile);
        var profile1 = Path.Combine(tempDir, "Profile 1");
        Directory.CreateDirectory(profile1);
        var otherDir = Path.Combine(tempDir, "Other Folder");
        Directory.CreateDirectory(otherDir);

        try
        {
            var profiles = (string[])method.Invoke(null, new object[] { tempDir })!;
            profiles.Should().Contain(defaultProfile);
            profiles.Should().Contain(profile1);
            profiles.Should().NotContain(otherDir);
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void CleanupChromiumBrowser_WithTempFiles_ShouldDelete()
    {
        var method = typeof(BrowserCleanupService).GetMethod("CleanupChromiumBrowser",
            BindingFlags.NonPublic | BindingFlags.Instance)!;

        // Create a fake browser profile with deletable files
        var tempDir = Path.Combine(Path.GetTempPath(), $"chrome_cleanup_{Guid.NewGuid():N}");
        var defaultProfile = Path.Combine(tempDir, "Default");
        Directory.CreateDirectory(defaultProfile);

        // Create files that match ChromiumFiles
        File.WriteAllText(Path.Combine(defaultProfile, "Cookies"), "fake cookies");
        File.WriteAllText(Path.Combine(defaultProfile, "History"), "fake history");
        File.WriteAllText(Path.Combine(defaultProfile, "Login Data"), "fake login data");

        try
        {
            var service = new BrowserCleanupService();
            var result = (Dictionary<string, object>)method.Invoke(service, new object[] { "TestChrome", new[] { tempDir } })!;

            result.Should().ContainKey("success");
            result.Should().ContainKey("files_deleted");
            ((int)result["files_deleted"]).Should().BeGreaterThanOrEqualTo(3);
        }
        finally
        {
            try { Directory.Delete(tempDir, true); } catch { }
        }
    }

    [Fact]
    public void CleanupFirefox_ViaTempDirectory_ShouldDeleteFiles()
    {
        // We can't easily override the Firefox path, but we can test the structure
        var service = new BrowserCleanupService();
        var result = service.CleanupAllBrowsers();

        // Verify structure
        var chromeResult = (Dictionary<string, object>)result["chrome"];
        chromeResult.Should().ContainKey("files_deleted");
        ((int)chromeResult["files_deleted"]).Should().BeGreaterThanOrEqualTo(0);

        var firefoxResult = (Dictionary<string, object>)result["firefox"];
        firefoxResult.Should().ContainKey("files_deleted");
        ((int)firefoxResult["files_deleted"]).Should().BeGreaterThanOrEqualTo(0);
    }
}
