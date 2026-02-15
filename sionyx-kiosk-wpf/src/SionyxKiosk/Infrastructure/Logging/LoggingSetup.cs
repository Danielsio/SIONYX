using System.IO;
using Serilog;
using Serilog.Events;

namespace SionyxKiosk.Infrastructure.Logging;

/// <summary>
/// Configures Serilog for the application with console + file sinks.
/// Replaces the Python SionyxLogger class.
/// </summary>
public static class LoggingSetup
{
    /// <summary>
    /// Initialize Serilog logging with console and file sinks.
    /// </summary>
    /// <param name="minLevel">Minimum log level (default: Information)</param>
    /// <param name="logToFile">Enable file logging (default: true)</param>
    public static void Initialize(LogEventLevel minLevel = LogEventLevel.Information, bool logToFile = true)
    {
        var logDir = GetLogDirectory();
        Directory.CreateDirectory(logDir);

        var today = DateTime.Now.ToString("yyyyMMdd");

        var config = new LoggerConfiguration()
            .MinimumLevel.Is(minLevel)
            .Enrich.WithProperty("Application", AppConstants.AppName)
            .Enrich.FromLogContext()
            .WriteTo.Console(
                outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {SourceContext,-20} {Message:lj}{NewLine}{Exception}",
                restrictedToMinimumLevel: minLevel);

        if (logToFile)
        {
            // Main log file (structured JSON)
            config.WriteTo.File(
                Path.Combine(logDir, $"sionyx_{today}.log"),
                outputTemplate: "{Timestamp:o} [{Level:u3}] {SourceContext} {Message:lj}{NewLine}{Exception}",
                restrictedToMinimumLevel: minLevel,
                encoding: System.Text.Encoding.UTF8);

            // Error-only log file
            config.WriteTo.File(
                Path.Combine(logDir, $"sionyx_errors_{today}.log"),
                restrictedToMinimumLevel: LogEventLevel.Error,
                encoding: System.Text.Encoding.UTF8);
        }

        Log.Logger = config.CreateLogger();

        Log.Information("");
        Log.Information("━━━ SIONYX ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        Log.Information("    Log Level: {Level}", minLevel);
        if (logToFile)
            Log.Information("    Log Dir:   {LogDir}", logDir);
        Log.Information("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        Log.Information("");
    }

    /// <summary>
    /// Remove log files older than the specified number of days.
    /// </summary>
    public static void CleanupOldLogs(int daysToKeep = 7)
    {
        var logDir = GetLogDirectory();
        if (!Directory.Exists(logDir)) return;

        var cutoff = DateTime.Now.AddDays(-daysToKeep);

        foreach (var file in Directory.GetFiles(logDir, "*.log"))
        {
            if (File.GetLastWriteTime(file) < cutoff)
            {
                try
                {
                    File.Delete(file);
                    Log.Debug("Deleted old log: {FileName}", Path.GetFileName(file));
                }
                catch (Exception ex)
                {
                    Log.Warning(ex, "Failed to delete old log: {FileName}", Path.GetFileName(file));
                }
            }
        }
    }

    private static string GetLogDirectory()
    {
        // Production: AppData/Local/SIONYX/logs
        // Development: project root / logs
        if (RegistryConfig.IsProduction())
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "SIONYX", "logs");
        }

        return Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
    }
}
