using System.Diagnostics;
using System.IO;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Closes user programs when a new session starts.
/// Ensures a clean state for each customer in kiosk environments.
/// </summary>
public class ProcessCleanupService
{
    private static readonly ILogger Logger = Log.ForContext<ProcessCleanupService>();

    /// <summary>Processes that should NEVER be killed.</summary>
    private static readonly HashSet<string> Whitelist = new(StringComparer.OrdinalIgnoreCase)
    {
        // SIONYX
        "sionyxkiosk.exe", "sionyx.exe", "dotnet.exe",
        // Windows core
        "system", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
        "lsass.exe", "svchost.exe", "winlogon.exe", "explorer.exe", "dwm.exe",
        "taskhostw.exe", "sihost.exe", "ctfmon.exe", "conhost.exe",
        "fontdrvhost.exe", "audiodg.exe", "runtimebroker.exe", "searchhost.exe",
        "startmenuexperiencehost.exe", "textinputhost.exe",
        "shellexperiencehost.exe", "applicationframehost.exe",
        "systemsettings.exe", "securityhealthservice.exe",
        "securityhealthsystray.exe", "msmpeng.exe", "nissrv.exe",
        "wuauclt.exe", "trustedinstaller.exe", "tiworker.exe",
        "dllhost.exe", "msiexec.exe", "spoolsv.exe", "searchindexer.exe",
        // Drivers
        "igfxem.exe", "igfxhk.exe", "igfxtray.exe", "nvcontainer.exe",
        // Utilities
        "onedrive.exe", "settingsynchost.exe",
    };

    /// <summary>User applications to specifically target for cleanup.</summary>
    private static readonly HashSet<string> Targets = new(StringComparer.OrdinalIgnoreCase)
    {
        // Browsers
        "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe", "iexplore.exe",
        // Office
        "winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe", "onenote.exe",
        "mspub.exe", "msaccess.exe",
        // Media
        "vlc.exe", "wmplayer.exe", "spotify.exe", "groove.exe", "itunes.exe",
        // Communication
        "teams.exe", "slack.exe", "discord.exe", "zoom.exe", "skype.exe",
        "telegram.exe", "whatsapp.exe",
        // Text editors
        "notepad.exe", "notepad++.exe", "wordpad.exe", "code.exe",
        // PDF
        "acrord32.exe", "acrobat.exe",
        // Image viewers
        "mspaint.exe",
        // Misc
        "calculator.exe", "snippingtool.exe",
    };

    /// <summary>Stubborn processes that should be killed by name.</summary>
    private static readonly HashSet<string> StubbornProcesses = new(StringComparer.OrdinalIgnoreCase)
    {
        "discord.exe", "teams.exe", "slack.exe", "zoom.exe",
    };

    /// <summary>Close all user processes that aren't in the whitelist.</summary>
    public Dictionary<string, object> CleanupUserProcesses()
    {
        Logger.Information("Starting user process cleanup for new session");

        var closedCount = 0;
        var failedCount = 0;
        var closedProcesses = new List<string>();
        var failedProcesses = new List<string>();

        var running = GetRunningProcesses();

        foreach (var (name, pids) in running)
        {
            if (Whitelist.Contains(name)) continue;
            if (!Targets.Contains(name)) continue;

            if (StubbornProcesses.Contains(name))
            {
                if (KillByName(name))
                {
                    closedCount += pids.Count;
                    if (!closedProcesses.Contains(name)) closedProcesses.Add(name);
                }
                else
                {
                    failedCount += pids.Count;
                    if (!failedProcesses.Contains(name)) failedProcesses.Add(name);
                }
            }
            else
            {
                foreach (var pid in pids)
                {
                    if (KillProcess(pid, name))
                    {
                        closedCount++;
                        if (!closedProcesses.Contains(name)) closedProcesses.Add(name);
                    }
                    else
                    {
                        failedCount++;
                        if (!failedProcesses.Contains(name)) failedProcesses.Add(name);
                    }
                }
            }
        }

        if (closedCount > 0)
            Logger.Information("Process cleanup: {Count} closed ({Processes})", closedCount, string.Join(", ", closedProcesses));
        else
            Logger.Information("No user processes found to clean up");

        return new Dictionary<string, object>
        {
            ["success"] = failedCount == 0,
            ["closed_count"] = closedCount,
            ["failed_count"] = failedCount,
            ["closed_processes"] = closedProcesses,
            ["failed_processes"] = failedProcesses,
        };
    }

    /// <summary>Close only browser processes.</summary>
    public Dictionary<string, object> CloseBrowsersOnly()
    {
        var browserNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe", "iexplore.exe",
        };

        var closedCount = 0;
        var running = GetRunningProcesses();

        foreach (var (name, pids) in running)
        {
            if (!browserNames.Contains(name)) continue;
            foreach (var pid in pids)
            {
                if (KillProcess(pid, name))
                    closedCount++;
            }
        }

        return new Dictionary<string, object> { ["success"] = true, ["closed_count"] = closedCount };
    }

    // ==================== PRIVATE ====================

    private static Dictionary<string, List<int>> GetRunningProcesses()
    {
        var processes = new Dictionary<string, List<int>>(StringComparer.OrdinalIgnoreCase);

        try
        {
            var si = new ProcessStartInfo
            {
                FileName = "tasklist",
                Arguments = "/FO CSV /NH",
                CreateNoWindow = true,
                UseShellExecute = false,
                RedirectStandardOutput = true,
            };

            using var proc = Process.Start(si);
            var output = proc?.StandardOutput.ReadToEnd() ?? "";
            proc?.WaitForExit(10000);

            foreach (var line in output.Split('\n', StringSplitOptions.RemoveEmptyEntries))
            {
                var parts = line.Split(',');
                if (parts.Length < 2) continue;
                var name = parts[0].Trim('"', ' ');
                if (int.TryParse(parts[1].Trim('"', ' '), out var pid))
                {
                    if (!processes.ContainsKey(name))
                        processes[name] = new List<int>();
                    processes[name].Add(pid);
                }
            }
        }
        catch (Exception ex)
        {
            Logger.Error("Error getting process list: {Error}", ex.Message);
        }

        return processes;
    }

    private static bool KillProcess(int pid, string name, int retryCount = 2)
    {
        for (var attempt = 0; attempt <= retryCount; attempt++)
        {
            try
            {
                var si = new ProcessStartInfo
                {
                    FileName = "taskkill",
                    Arguments = $"/PID {pid} /F /T",
                    CreateNoWindow = true,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                };

                using var proc = Process.Start(si);
                proc?.WaitForExit(5000);

                if (proc?.ExitCode == 0) return true;

                var stderr = proc?.StandardError.ReadToEnd() ?? "";
                if (stderr.Contains("not found", StringComparison.OrdinalIgnoreCase)) return true;

                if (attempt < retryCount)
                    Thread.Sleep(200);
            }
            catch (Exception ex)
            {
                Logger.Error("Error killing process {Name}: {Error}", name, ex.Message);
                return false;
            }
        }
        return false;
    }

    private static bool KillByName(string processName)
    {
        try
        {
            var si = new ProcessStartInfo
            {
                FileName = "taskkill",
                Arguments = $"/IM {processName} /F /T",
                CreateNoWindow = true,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
            };

            using var proc = Process.Start(si);
            proc?.WaitForExit(10000);

            if (proc?.ExitCode == 0) return true;
            var stderr = proc?.StandardError.ReadToEnd() ?? "";
            return stderr.Contains("not found", StringComparison.OrdinalIgnoreCase);
        }
        catch (Exception ex)
        {
            Logger.Error("Error killing by name {Name}: {Error}", processName, ex.Message);
            return false;
        }
    }
}
