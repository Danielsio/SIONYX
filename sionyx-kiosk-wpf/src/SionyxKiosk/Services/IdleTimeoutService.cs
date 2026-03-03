using System.Runtime.InteropServices;
using System.Windows.Threading;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Detects system-wide user inactivity using Windows GetLastInputInfo API.
/// Fires warnings before auto-ending an idle session to prevent wasted time.
/// </summary>
public class IdleTimeoutService : IDisposable
{
    private static readonly ILogger Logger = Log.ForContext<IdleTimeoutService>();

    [StructLayout(LayoutKind.Sequential)]
    private struct LASTINPUTINFO
    {
        public uint cbSize;
        public uint dwTime;
    }

    [DllImport("user32.dll")]
    private static extern bool GetLastInputInfo(ref LASTINPUTINFO plii);

    public int WarningIdleSeconds { get; set; } = 180;
    public int MaxIdleSeconds { get; set; } = 300;

    public event Action<int>? IdleWarning;
    public event Action? IdleTimeout;
    public event Action? ActivityResumed;

    private readonly DispatcherTimer _checkTimer;
    private bool _warningFired;
    private bool _isMonitoring;
    private DateTime _manualResetTime = DateTime.MinValue;

    public IdleTimeoutService()
    {
        _checkTimer = new DispatcherTimer
        {
            Interval = TimeSpan.FromSeconds(30)
        };
        _checkTimer.Tick += (_, _) => CheckIdleState();
    }

    public void StartMonitoring()
    {
        if (_isMonitoring) return;
        _isMonitoring = true;
        _warningFired = false;
        _manualResetTime = DateTime.UtcNow;
        _checkTimer.Start();
        Logger.Information("Idle timeout monitoring started (warn={Warn}s, max={Max}s)",
            WarningIdleSeconds, MaxIdleSeconds);
    }

    public void StopMonitoring()
    {
        if (!_isMonitoring) return;
        _isMonitoring = false;
        _warningFired = false;
        _checkTimer.Stop();
        Logger.Information("Idle timeout monitoring stopped");
    }

    public void ResetActivity()
    {
        _manualResetTime = DateTime.UtcNow;
        if (_warningFired)
        {
            _warningFired = false;
            ActivityResumed?.Invoke();
        }
    }

    private void CheckIdleState()
    {
        if (!_isMonitoring) return;

        var idleSeconds = GetIdleSeconds();
        if (idleSeconds < 0) return;

        if (idleSeconds >= MaxIdleSeconds)
        {
            Logger.Warning("Idle timeout reached ({Seconds}s), ending session", idleSeconds);
            StopMonitoring();
            IdleTimeout?.Invoke();
            return;
        }

        if (idleSeconds >= WarningIdleSeconds && !_warningFired)
        {
            _warningFired = true;
            var remaining = MaxIdleSeconds - idleSeconds;
            Logger.Information("Idle warning: {Remaining}s until timeout", remaining);
            IdleWarning?.Invoke(remaining);
            return;
        }

        if (idleSeconds < WarningIdleSeconds && _warningFired)
        {
            _warningFired = false;
            Logger.Information("User activity resumed after idle warning");
            ActivityResumed?.Invoke();
        }
    }

    private int GetIdleSeconds()
    {
        var info = new LASTINPUTINFO { cbSize = (uint)Marshal.SizeOf<LASTINPUTINFO>() };
        if (!GetLastInputInfo(ref info))
            return -1;

        var lastInputTicks = info.dwTime;
        var currentTicks = (uint)Environment.TickCount;
        var idleMs = currentTicks - lastInputTicks;
        var idleSeconds = (int)(idleMs / 1000);

        // If there was a manual reset more recently than the last system input,
        // treat the manual reset as the last activity
        var msSinceReset = (DateTime.UtcNow - _manualResetTime).TotalMilliseconds;
        if (msSinceReset < idleMs)
            idleSeconds = (int)(msSinceReset / 1000);

        return idleSeconds;
    }

    public void Dispose()
    {
        StopMonitoring();
        GC.SuppressFinalize(this);
    }
}
