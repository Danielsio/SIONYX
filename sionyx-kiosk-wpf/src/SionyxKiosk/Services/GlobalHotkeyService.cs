using System.Runtime.InteropServices;
using System.Windows.Interop;
using SionyxKiosk.Infrastructure;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Global hotkey service using Win32 RegisterHotKey API.
/// Simpler and more reliable than the Python 'keyboard' library.
/// </summary>
public class GlobalHotkeyService : IDisposable
{
    private static readonly ILogger Logger = Log.ForContext<GlobalHotkeyService>();

    // P/Invoke
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

    // Modifier keys
    private const uint MOD_ALT = 0x0001;
    private const uint MOD_CONTROL = 0x0002;
    private const uint MOD_SHIFT = 0x0004;
    private const uint MOD_NOREPEAT = 0x4000;

    // Virtual keys
    private const uint VK_SPACE = 0x20;
    private const uint VK_Q = 0x51;

    // Windows message
    private const int WM_HOTKEY = 0x0312;

    // Hotkey IDs
    private const int HOTKEY_ADMIN_EXIT_PRIMARY = 9001;
    private const int HOTKEY_ADMIN_EXIT_LEGACY = 9002;

    private IntPtr _windowHandle = IntPtr.Zero;
    private HwndSource? _hwndSource;
    private bool _isRunning;

    // Events
    public event Action? AdminExitRequested;

    public string AdminExitHotkey { get; }
    public bool IsRunning => _isRunning;

    public GlobalHotkeyService()
    {
        AdminExitHotkey = ResolveAdminExitHotkey();
    }

    /// <summary>Register hotkeys with a WPF window handle.</summary>
    public void Start(IntPtr windowHandle)
    {
        if (_isRunning)
        {
            Logger.Warning("Global hotkey service already running");
            return;
        }

        if (windowHandle == IntPtr.Zero)
        {
            Logger.Error("Cannot start global hotkey service: window handle is zero");
            return;
        }

        _windowHandle = windowHandle;

        // Hook into window message processing
        _hwndSource = HwndSource.FromHwnd(windowHandle);
        if (_hwndSource == null)
        {
            Logger.Error("HwndSource.FromHwnd returned null for handle {Handle}", windowHandle);
            return;
        }
        _hwndSource.AddHook(WndProc);

        // Register primary hotkey: Ctrl+Alt+Space (or configured)
        var (primaryMod, primaryVk) = ParseHotkey(AdminExitHotkey);
        var primaryOk = RegisterHotKey(_windowHandle, HOTKEY_ADMIN_EXIT_PRIMARY, primaryMod | MOD_NOREPEAT, primaryVk);
        if (!primaryOk)
        {
            var err = Marshal.GetLastWin32Error();
            Logger.Error("Failed to register primary hotkey ({Hotkey}): Win32 error {Error}", AdminExitHotkey, err);
        }
        else
        {
            Logger.Information("Registered primary hotkey: {Hotkey}", AdminExitHotkey);
        }

        // Register legacy hotkey: Ctrl+Alt+Q
        var legacyOk = RegisterHotKey(_windowHandle, HOTKEY_ADMIN_EXIT_LEGACY, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_Q);
        if (!legacyOk)
        {
            var err = Marshal.GetLastWin32Error();
            Logger.Error("Failed to register legacy hotkey (Ctrl+Alt+Q): Win32 error {Error}", err);
        }
        else
        {
            Logger.Information("Registered legacy hotkey: Ctrl+Alt+Q");
        }

        _isRunning = primaryOk || legacyOk;
        if (_isRunning)
            Logger.Information("Global hotkey service started");
        else
            Logger.Error("Global hotkey service FAILED to register any hotkeys");
    }

    /// <summary>Stop and unregister hotkeys.</summary>
    public void Stop()
    {
        if (!_isRunning) return;

        UnregisterHotKey(_windowHandle, HOTKEY_ADMIN_EXIT_PRIMARY);
        UnregisterHotKey(_windowHandle, HOTKEY_ADMIN_EXIT_LEGACY);

        _hwndSource?.RemoveHook(WndProc);
        _hwndSource = null;
        _isRunning = false;

        Logger.Information("Global hotkey service stopped");
    }

    public void Dispose()
    {
        Stop();
        GC.SuppressFinalize(this);
    }

    // ==================== PRIVATE ====================

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (msg == WM_HOTKEY)
        {
            var id = wParam.ToInt32();
            if (id is HOTKEY_ADMIN_EXIT_PRIMARY or HOTKEY_ADMIN_EXIT_LEGACY)
            {
                Logger.Information("Admin exit hotkey pressed");
                AdminExitRequested?.Invoke();
                handled = true;
            }
        }
        return IntPtr.Zero;
    }

    private static string ResolveAdminExitHotkey()
    {
        // Try registry first (production)
        var registryValue = RegistryConfig.ReadValue("AdminExitHotkey");
        if (!string.IsNullOrEmpty(registryValue))
            return registryValue.Trim().ToLower().Replace(" ", "");

        // Try environment variable
        var envValue = Environment.GetEnvironmentVariable("ADMIN_EXIT_HOTKEY");
        if (!string.IsNullOrEmpty(envValue))
            return envValue.Trim().ToLower().Replace(" ", "");

        return AppConstants.AdminExitHotkeyDefault;
    }

    private static (uint modifiers, uint vk) ParseHotkey(string hotkey)
    {
        uint mod = 0;
        uint vk = VK_SPACE; // default

        var parts = hotkey.ToLower().Replace(" ", "").Split('+');
        foreach (var part in parts)
        {
            switch (part)
            {
                case "ctrl": mod |= MOD_CONTROL; break;
                case "alt": mod |= MOD_ALT; break;
                case "shift": mod |= MOD_SHIFT; break;
                case "space": vk = VK_SPACE; break;
                case "q": vk = VK_Q; break;
                default:
                    // Try to parse single character as virtual key
                    if (part.Length == 1 && char.IsLetter(part[0]))
                        vk = (uint)char.ToUpper(part[0]);
                    break;
            }
        }

        return (mod, vk);
    }
}
