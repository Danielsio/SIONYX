using System.Diagnostics;
using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FlaUI.UIA3;

namespace SionyxKiosk.E2E.Fixtures;

public class KioskAppFixture : IDisposable
{
    public Application App { get; }
    public UIA3Automation Automation { get; } = new();
    public string? LaunchError { get; private set; }

    private bool _loginAttempted;
    private bool _loginSucceeded;
    private readonly object _loginLock = new();

    public KioskAppFixture()
    {
        KillExisting();
        var exePath = FindExe();
        App = Application.Launch(exePath);

        Thread.Sleep(5000);

        try
        {
            if (App.HasExited)
            {
                LaunchError = $"App exited immediately with code {App.ExitCode}. " +
                              $"Exe: {exePath}. Check .env file and Firebase config.";
            }
        }
        catch (InvalidOperationException)
        {
            LaunchError = $"App process not associated (crashed on startup). Exe: {exePath}";
        }
    }

    /// <summary>
    /// Performs login once if credentials are available and login hasn't been done yet.
    /// Returns true if logged in (or already was), false if no credentials.
    /// </summary>
    public bool EnsureLoggedIn()
    {
        lock (_loginLock)
        {
            if (_loginSucceeded)
                return true;

            if (_loginAttempted)
                return _loginSucceeded;

            var phone = Environment.GetEnvironmentVariable("SIONYX_E2E_PHONE");
            var password = Environment.GetEnvironmentVariable("SIONYX_E2E_PASSWORD");
            if (string.IsNullOrEmpty(phone) || string.IsNullOrEmpty(password))
                return false;

            // Already on main window (e.g. auto-login)?
            var existing = WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(2), exact: true);
            if (existing != null)
            {
                _loginAttempted = true;
                _loginSucceeded = true;
                return true;
            }

            _loginAttempted = true;

            var authWindow = GetAuthWindow();

            var phoneInput = authWindow.FindFirstDescendant(
                cf => cf.ByAutomationId("LoginPhoneInput"))?.AsTextBox();
            if (phoneInput == null) return false;
            phoneInput.Text = phone;

            var passwordInput = authWindow.FindFirstDescendant(
                cf => cf.ByAutomationId("LoginPasswordInput"));
            if (passwordInput == null) return false;
            passwordInput.Focus();
            Thread.Sleep(100);
            // WPF PasswordBox ignores Ctrl+A; use Home then Shift+End to select all
            Keyboard.Press(FlaUI.Core.WindowsAPI.VirtualKeyShort.HOME);
            Thread.Sleep(50);
            Keyboard.TypeSimultaneously(FlaUI.Core.WindowsAPI.VirtualKeyShort.SHIFT,
                                         FlaUI.Core.WindowsAPI.VirtualKeyShort.END);
            Thread.Sleep(50);
            Keyboard.Type(password);

            var loginButton = authWindow.FindFirstDescendant(
                cf => cf.ByAutomationId("LoginButton"))?.AsButton();
            if (loginButton == null) return false;
            loginButton.Click();

            var mainWindow = WaitForWindowByTitle("SIONYX", TimeSpan.FromSeconds(30), exact: true);
            _loginSucceeded = mainWindow != null;
            return _loginSucceeded;
        }
    }

    public Window GetAuthWindow(TimeSpan? timeout = null)
    {
        if (LaunchError != null)
            throw new InvalidOperationException($"App failed to start: {LaunchError}");

        var deadline = DateTime.UtcNow + (timeout ?? TimeSpan.FromSeconds(30));
        Exception? lastError = null;

        while (DateTime.UtcNow < deadline)
        {
            try
            {
                return App.GetMainWindow(Automation, TimeSpan.FromSeconds(5));
            }
            catch (Exception ex) when (ex.Message.Contains("E_FAIL") || ex.Message.Contains("COM"))
            {
                lastError = ex;
                Thread.Sleep(1000);
            }
        }

        throw new InvalidOperationException(
            $"Failed to get auth window after retries: {lastError?.Message}", lastError);
    }

    public Window? WaitForWindowByTitle(string title, TimeSpan? timeout = null, bool exact = false)
    {
        var deadline = DateTime.UtcNow + (timeout ?? TimeSpan.FromSeconds(30));
        while (DateTime.UtcNow < deadline)
        {
            try
            {
                var windows = App.GetAllTopLevelWindows(Automation);
                var match = exact
                    ? windows.FirstOrDefault(w =>
                        string.Equals(w.Title, title, StringComparison.OrdinalIgnoreCase))
                    : windows.FirstOrDefault(w =>
                        w.Title?.Contains(title, StringComparison.OrdinalIgnoreCase) == true);
                if (match != null) return match;
            }
            catch
            {
                // COM errors can happen transiently
            }
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
