using System.Diagnostics;
using System.Windows.Threading;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Monitors and terminates unauthorized processes (regedit, cmd, PowerShell, etc.).
/// Uses DispatcherTimer for periodic polling.
/// </summary>
public class ProcessRestrictionService : IDisposable
{
    private static readonly ILogger Logger = Log.ForContext<ProcessRestrictionService>();

    /// <summary>Default blacklisted processes.</summary>
    private static readonly HashSet<string> DefaultBlacklist = new(StringComparer.OrdinalIgnoreCase)
    {
        // System tools
        "regedit.exe", "cmd.exe", "powershell.exe", "pwsh.exe",
        "mmc.exe", "taskmgr.exe", "control.exe", "msconfig.exe",
        "gpedit.msc", "secpol.msc", "compmgmt.msc", "devmgmt.msc",
        "diskmgmt.msc", "services.msc",
        // Script hosts
        "wscript.exe", "cscript.exe", "mshta.exe",
        "certutil.exe", "bitsadmin.exe", "wmic.exe",
        // Remote access
        "teamviewer.exe", "anydesk.exe", "ultraviewer.exe",
    };

    private readonly HashSet<string> _blacklist;
    private readonly DispatcherTimer _checkTimer;
    private readonly HashSet<int> _recentlyBlocked = new();

    public bool Enabled { get; set; }
    public bool IsActive => _checkTimer.IsEnabled && Enabled;

    // Events
    public event Action<string>? ProcessBlocked;  // blocked process name
    public event Action<string>? ErrorOccurred;

    public ProcessRestrictionService(
        HashSet<string>? blacklist = null,
        int checkIntervalMs = 2000,
        bool enabled = true)
    {
        Enabled = enabled;
        _blacklist = blacklist ?? new HashSet<string>(DefaultBlacklist, StringComparer.OrdinalIgnoreCase);
        _checkTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(checkIntervalMs) };
        _checkTimer.Tick += (_, _) => CheckProcesses();
    }

    public void Start()
    {
        if (!Enabled)
        {
            Logger.Information("Process restriction disabled");
            return;
        }

        Logger.Information("Starting process restriction (blacklist: {Count})", _blacklist.Count);
        _checkTimer.Start();
        CheckProcesses(); // Initial check
    }

    public void Stop()
    {
        Logger.Information("Stopping process restriction");
        _checkTimer.Stop();
    }

    public void AddToBlacklist(string processName) => _blacklist.Add(processName.ToLower());
    public void RemoveFromBlacklist(string processName) => _blacklist.Remove(processName.ToLower());
    public List<string> GetBlacklist() => _blacklist.OrderBy(x => x).ToList();

    public void Dispose()
    {
        Stop();
        GC.SuppressFinalize(this);
    }

    // ==================== PRIVATE ====================

    private void CheckProcesses()
    {
        if (!Enabled) return;

        try
        {
            foreach (var proc in Process.GetProcesses())
            {
                try
                {
                    var name = proc.ProcessName + ".exe";
                    var pid = proc.Id;

                    if (_recentlyBlocked.Contains(pid)) continue;
                    if (!_blacklist.Contains(name)) continue;

                    TerminateProcess(proc, name);
                }
                catch (InvalidOperationException)
                {
                    // Process ended
                }
                catch (System.ComponentModel.Win32Exception)
                {
                    // Access denied
                }
                finally
                {
                    proc.Dispose();
                }
            }

            CleanupBlockedSet();
        }
        catch (Exception ex)
        {
            Logger.Error("Error checking processes: {Error}", ex.Message);
        }
    }

    private void TerminateProcess(Process proc, string name)
    {
        try
        {
            Logger.Warning("Terminating unauthorized process: {Name} (PID: {Pid})", name, proc.Id);

            proc.Kill(entireProcessTree: true);

            _recentlyBlocked.Add(proc.Id);
            ProcessBlocked?.Invoke(name);
            Logger.Information("Successfully terminated: {Name}", name);
        }
        catch (InvalidOperationException)
        {
            // Already gone
        }
        catch (System.ComponentModel.Win32Exception)
        {
            _recentlyBlocked.Add(proc.Id);
            Logger.Warning("Access denied terminating {Name}. User may be admin.", name);
            ErrorOccurred?.Invoke($"Cannot terminate {name} - access denied");
        }
        catch (Exception ex)
        {
            Logger.Error("Error terminating {Name}: {Error}", name, ex.Message);
            ErrorOccurred?.Invoke($"Error blocking {name}");
        }
    }

    private void CleanupBlockedSet()
    {
        var runningPids = new HashSet<int>();
        foreach (var p in Process.GetProcesses())
        {
            try { runningPids.Add(p.Id); }
            catch { /* ignored */ }
            finally { p.Dispose(); }
        }
        _recentlyBlocked.IntersectWith(runningPids);
    }
}
