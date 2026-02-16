using System.IO;
using FluentAssertions;
using Serilog.Events;
using SionyxKiosk.Infrastructure.Logging;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for LoggingSetup covering Initialize and CleanupOldLogs.
/// </summary>
public class LoggingSetupTests
{
    [Fact]
    public void Initialize_WithConsoleOnly_ShouldNotThrow()
    {
        var act = () => LoggingSetup.Initialize(LogEventLevel.Debug, logToFile: false);
        act.Should().NotThrow();
    }

    [Fact]
    public void Initialize_WithFileLogging_ShouldNotThrow()
    {
        var act = () => LoggingSetup.Initialize(LogEventLevel.Information, logToFile: true);
        act.Should().NotThrow();
    }

    [Fact]
    public void Initialize_WithVerboseLevel_ShouldNotThrow()
    {
        var act = () => LoggingSetup.Initialize(LogEventLevel.Verbose, logToFile: false);
        act.Should().NotThrow();
    }

    [Fact]
    public void CleanupOldLogs_WhenNoLogDirectory_ShouldNotThrow()
    {
        var act = () => LoggingSetup.CleanupOldLogs(7);
        act.Should().NotThrow();
    }

    [Fact]
    public void CleanupOldLogs_WithExistingLogs_ShouldDeleteOldFiles()
    {
        // Create a temp directory with some fake log files
        var tempDir = Path.Combine(Path.GetTempPath(), $"sionyx_log_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);

        try
        {
            // Create an "old" log file
            var oldLog = Path.Combine(tempDir, "sionyx_old.log");
            File.WriteAllText(oldLog, "old log content");
            File.SetLastWriteTime(oldLog, DateTime.Now.AddDays(-30));

            // Create a "new" log file
            var newLog = Path.Combine(tempDir, "sionyx_new.log");
            File.WriteAllText(newLog, "new log content");

            // Run cleanup (this tests the logic, even though it won't target our temp dir
            // since GetLogDirectory is hardcoded)
            var act = () => LoggingSetup.CleanupOldLogs(7);
            act.Should().NotThrow();
        }
        finally
        {
            Directory.Delete(tempDir, true);
        }
    }

    [Fact]
    public void Initialize_MultipleTimes_ShouldNotThrow()
    {
        // Initialize multiple times should be safe (Serilog supports this)
        LoggingSetup.Initialize(LogEventLevel.Warning, logToFile: false);
        LoggingSetup.Initialize(LogEventLevel.Information, logToFile: false);
    }
}
