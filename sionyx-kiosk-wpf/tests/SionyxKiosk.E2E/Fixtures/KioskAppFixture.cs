using System.Diagnostics;
using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;

namespace SionyxKiosk.E2E.Fixtures;

public class KioskAppFixture : IDisposable
{
    public Application App { get; }
    public UIA3Automation Automation { get; } = new();

    public KioskAppFixture()
    {
        KillExisting();
        App = Application.Launch(FindExe());
    }

    public Window GetAuthWindow(TimeSpan? timeout = null)
    {
        return App.GetMainWindow(Automation, timeout ?? TimeSpan.FromSeconds(30));
    }

    public Window? WaitForWindowByTitle(string titleFragment, TimeSpan? timeout = null)
    {
        var deadline = DateTime.UtcNow + (timeout ?? TimeSpan.FromSeconds(30));
        while (DateTime.UtcNow < deadline)
        {
            var windows = App.GetAllTopLevelWindows(Automation);
            var match = windows.FirstOrDefault(w =>
                w.Title?.Contains(titleFragment, StringComparison.OrdinalIgnoreCase) == true);
            if (match != null) return match;
            Thread.Sleep(500);
        }
        return null;
    }

    private static void KillExisting()
    {
        foreach (var p in Process.GetProcessesByName("SionyxKiosk"))
        {
            try { p.Kill(); p.WaitForExit(5000); } catch { /* best effort */ }
        }
    }

    private static string FindExe()
    {
        var envPath = Environment.GetEnvironmentVariable("SIONYX_EXE_PATH");
        if (!string.IsNullOrEmpty(envPath))
        {
            if (File.Exists(envPath)) return Path.GetFullPath(envPath);

            var fromCwd = Path.Combine(Directory.GetCurrentDirectory(), envPath);
            if (File.Exists(fromCwd)) return Path.GetFullPath(fromCwd);
        }

        var dir = AppDomain.CurrentDomain.BaseDirectory;
        for (int i = 0; i < 10; i++)
        {
            var parent = Path.GetDirectoryName(dir);
            if (parent == null || parent == dir) break;
            dir = parent;

            foreach (var config in new[] { "Debug", "Release" })
            {
                var candidate = Path.Combine(dir, "src", "SionyxKiosk", "bin", config, "net8.0-windows", "SionyxKiosk.exe");
                if (File.Exists(candidate)) return candidate;
            }
        }

        throw new FileNotFoundException(
            "SionyxKiosk.exe not found. Build the app first or set SIONYX_EXE_PATH.");
    }

    public void Dispose()
    {
        try { App.Close(); } catch { /* best effort */ }
        try { App.Dispose(); } catch { /* best effort */ }
        Automation.Dispose();
        KillExisting();
    }
}
