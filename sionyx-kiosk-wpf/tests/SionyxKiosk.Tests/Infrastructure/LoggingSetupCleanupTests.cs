using System.IO;
using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure.Logging;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests targeting LoggingSetup.CleanupOldLogs with actual old files
/// and GetLogDirectory for different production modes.
/// </summary>
public class LoggingSetupCleanupTests
{
    [Fact]
    public void GetLogDirectory_ShouldReturnValidPath()
    {
        var method = typeof(LoggingSetup).GetMethod("GetLogDirectory",
            BindingFlags.NonPublic | BindingFlags.Static)!;

        var result = (string)method.Invoke(null, null)!;
        result.Should().NotBeNullOrEmpty();
        // Should be a valid directory path
        Path.IsPathRooted(result).Should().BeTrue();
    }

    [Fact]
    public void CleanupOldLogs_WithOldFiles_ShouldDeleteThem()
    {
        // Get the actual log directory used by the app
        var getLogDir = typeof(LoggingSetup).GetMethod("GetLogDirectory",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var logDir = (string)getLogDir.Invoke(null, null)!;
        Directory.CreateDirectory(logDir);

        // Create an old log file
        var oldLogFile = Path.Combine(logDir, $"test_old_cleanup_{Guid.NewGuid():N}.log");
        File.WriteAllText(oldLogFile, "old log data");

        // Set the file's last write time to 30 days ago
        File.SetLastWriteTime(oldLogFile, DateTime.Now.AddDays(-30));

        try
        {
            // Clean up with 7-day retention
            LoggingSetup.CleanupOldLogs(daysToKeep: 7);

            // The old file should be deleted
            File.Exists(oldLogFile).Should().BeFalse();
        }
        finally
        {
            // Ensure cleanup
            try { File.Delete(oldLogFile); } catch { }
        }
    }

    [Fact]
    public void CleanupOldLogs_WithRecentFiles_ShouldKeepThem()
    {
        var getLogDir = typeof(LoggingSetup).GetMethod("GetLogDirectory",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var logDir = (string)getLogDir.Invoke(null, null)!;
        Directory.CreateDirectory(logDir);

        // Create a recent log file
        var recentLogFile = Path.Combine(logDir, $"test_recent_cleanup_{Guid.NewGuid():N}.log");
        File.WriteAllText(recentLogFile, "recent log data");
        // File is already recent (just created)

        try
        {
            LoggingSetup.CleanupOldLogs(daysToKeep: 7);

            // The recent file should NOT be deleted
            File.Exists(recentLogFile).Should().BeTrue();
        }
        finally
        {
            try { File.Delete(recentLogFile); } catch { }
        }
    }

    [Fact]
    public void CleanupOldLogs_WithZeroDays_ShouldDeleteAllLogs()
    {
        var getLogDir = typeof(LoggingSetup).GetMethod("GetLogDirectory",
            BindingFlags.NonPublic | BindingFlags.Static)!;
        var logDir = (string)getLogDir.Invoke(null, null)!;
        Directory.CreateDirectory(logDir);

        // Create a file that was written 1 day ago
        var logFile = Path.Combine(logDir, $"test_zero_day_{Guid.NewGuid():N}.log");
        File.WriteAllText(logFile, "data");
        File.SetLastWriteTime(logFile, DateTime.Now.AddDays(-1));

        try
        {
            LoggingSetup.CleanupOldLogs(daysToKeep: 0);
            File.Exists(logFile).Should().BeFalse();
        }
        finally
        {
            try { File.Delete(logFile); } catch { }
        }
    }
}
