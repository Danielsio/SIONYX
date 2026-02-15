using System.Diagnostics;
using System.IO;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Clears browser cookies and session data on session end.
/// Prevents next user from accessing previous user's accounts.
/// </summary>
public class BrowserCleanupService
{
    private static readonly ILogger Logger = Log.ForContext<BrowserCleanupService>();

    private static readonly ProcessStartInfo HiddenStartInfo = new()
    {
        CreateNoWindow = true,
        UseShellExecute = false,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
    };

    // Chromium files to delete (sensitive session data)
    private static readonly string[] ChromiumFiles =
    [
        "Cookies", "Cookies-journal", "Login Data", "Login Data-journal",
        "Web Data", "Web Data-journal", "History", "History-journal",
        "Sessions", "Current Session", "Current Tabs",
        "Last Session", "Last Tabs",
    ];

    // Firefox files to delete
    private static readonly string[] FirefoxFiles =
    [
        "cookies.sqlite", "cookies.sqlite-wal", "cookies.sqlite-shm",
        "logins.json", "key4.db", "signons.sqlite",
        "sessionstore.jsonlz4", "sessionstore-backups",
    ];

    /// <summary>Close browsers first, then clean up. Recommended for session end.</summary>
    public Dictionary<string, object> CleanupWithBrowserClose()
    {
        Logger.Information("Closing browsers before cleanup...");

        var closeResults = CloseBrowsers();
        Thread.Sleep(1000); // Let browsers finish closing

        var results = CleanupAllBrowsers();
        results["browsers_closed"] = closeResults;
        return results;
    }

    /// <summary>Clean up all supported browsers.</summary>
    public Dictionary<string, object> CleanupAllBrowsers()
    {
        Logger.Information("Starting browser cleanup for all browsers");

        var results = new Dictionary<string, object>
        {
            ["success"] = true,
            ["chrome"] = CleanupChromiumBrowser("Chrome", GetChromePaths()),
            ["edge"] = CleanupChromiumBrowser("Edge", GetEdgePaths()),
            ["firefox"] = CleanupFirefox(),
        };

        return results;
    }

    /// <summary>Close all browsers gracefully.</summary>
    public Dictionary<string, bool> CloseBrowsers()
    {
        var results = new Dictionary<string, bool>();
        var browsers = new Dictionary<string, string>
        {
            ["chrome"] = "chrome.exe",
            ["edge"] = "msedge.exe",
            ["firefox"] = "firefox.exe",
        };

        // Single tasklist call to detect all running browsers
        string runningOutput;
        try
        {
            var si = CloneStartInfo();
            si.FileName = "tasklist";
            si.Arguments = "/FO CSV";
            using var process = Process.Start(si);
            runningOutput = process?.StandardOutput.ReadToEnd().ToLower() ?? "";
            process?.WaitForExit(5000);
        }
        catch
        {
            runningOutput = "";
        }

        foreach (var (name, processName) in browsers)
        {
            if (runningOutput.Contains(processName.ToLower()))
            {
                try
                {
                    var si = CloneStartInfo();
                    si.FileName = "taskkill";
                    si.Arguments = $"/IM {processName} /F";
                    using var p = Process.Start(si);
                    p?.WaitForExit(10000);
                    results[name] = true;
                    Logger.Information("Closed {Browser}", name);
                }
                catch (Exception ex)
                {
                    results[name] = false;
                    Logger.Warning("Failed to close {Browser}: {Error}", name, ex.Message);
                }
            }
            else
            {
                results[name] = true; // Already closed
            }
        }

        return results;
    }

    // ==================== PRIVATE ====================

    private Dictionary<string, object> CleanupChromiumBrowser(string browserName, string[] basePaths)
    {
        var filesDeleted = 0;
        var errors = new List<string>();

        foreach (var basePath in basePaths)
        {
            if (!Directory.Exists(basePath)) continue;

            var profiles = FindChromiumProfiles(basePath);
            foreach (var profile in profiles)
            {
                foreach (var fileName in ChromiumFiles)
                {
                    var filePath = Path.Combine(profile, fileName);
                    filesDeleted += TryDeleteFileOrDir(filePath, browserName, errors);
                }
            }
        }

        Logger.Information("{Browser}: Cleanup complete, {Count} files deleted", browserName, filesDeleted);
        return new Dictionary<string, object>
        {
            ["success"] = errors.Count == 0,
            ["files_deleted"] = filesDeleted,
        };
    }

    private Dictionary<string, object> CleanupFirefox()
    {
        var filesDeleted = 0;
        var errors = new List<string>();
        var profilesPath = GetFirefoxProfilesPath();

        if (Directory.Exists(profilesPath))
        {
            foreach (var profileDir in Directory.GetDirectories(profilesPath))
            {
                foreach (var fileName in FirefoxFiles)
                {
                    var filePath = Path.Combine(profileDir, fileName);
                    filesDeleted += TryDeleteFileOrDir(filePath, "Firefox", errors);
                }
            }
        }

        Logger.Information("Firefox: Cleanup complete, {Count} files deleted", filesDeleted);
        return new Dictionary<string, object>
        {
            ["success"] = errors.Count == 0,
            ["files_deleted"] = filesDeleted,
        };
    }

    private static int TryDeleteFileOrDir(string path, string browser, List<string> errors)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
                return 1;
            }
            if (Directory.Exists(path))
            {
                Directory.Delete(path, recursive: true);
                return 1;
            }
        }
        catch (UnauthorizedAccessException)
        {
            errors.Add($"Permission denied: {path}");
            Logger.Warning("{Browser}: Cannot delete {Path} (browser may be running)", browser, path);
        }
        catch (Exception ex)
        {
            errors.Add($"Error deleting {path}: {ex.Message}");
        }
        return 0;
    }

    private static string[] FindChromiumProfiles(string basePath)
    {
        var profiles = new List<string>();
        var defaultProfile = Path.Combine(basePath, "Default");
        if (Directory.Exists(defaultProfile))
            profiles.Add(defaultProfile);

        foreach (var dir in Directory.GetDirectories(basePath))
        {
            if (Path.GetFileName(dir).StartsWith("Profile "))
                profiles.Add(dir);
        }
        return profiles.ToArray();
    }

    private static string[] GetChromePaths()
    {
        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        return [Path.Combine(localAppData, "Google", "Chrome", "User Data")];
    }

    private static string[] GetEdgePaths()
    {
        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        return [Path.Combine(localAppData, "Microsoft", "Edge", "User Data")];
    }

    private static string GetFirefoxProfilesPath()
    {
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        return Path.Combine(appData, "Mozilla", "Firefox", "Profiles");
    }

    private static ProcessStartInfo CloneStartInfo() => new()
    {
        CreateNoWindow = true,
        UseShellExecute = false,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
    };
}
