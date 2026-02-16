using System.Runtime.InteropServices;
using System.Windows.Interop;
using SionyxKiosk.Infrastructure;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Global hotkey service using a low-level keyboard hook (WH_KEYBOARD_LL).
/// This is more reliable than RegisterHotKey because it works regardless of
/// which window has focus or whether the target window is minimized.
/// </summary>
public class GlobalHotkeyService : IDisposable
{
    private static readonly ILogger Logger = Log.ForContext<GlobalHotkeyService>();

    // P/Invoke — low-level keyboard hook
    private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr GetModuleHandle(string? lpModuleName);

    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int vKey);

    // Win32 constants
    private const int WH_KEYBOARD_LL = 13;
    private const int WM_KEYDOWN = 0x0100;
    private const int WM_SYSKEYDOWN = 0x0104;
    private const int VK_SPACE = 0x20;
    private const int VK_Q = 0x51;
    private const int VK_MENU = 0x12;    // Alt
    private const int VK_CONTROL = 0x11; // Ctrl

    [StructLayout(LayoutKind.Sequential)]
    private struct KBDLLHOOKSTRUCT
    {
        public uint vkCode;
        public uint scanCode;
        public uint flags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    private IntPtr _hookHandle = IntPtr.Zero;
    private LowLevelKeyboardProc? _hookProc; // prevent GC collection
    private bool _isRunning;

    // Events
    public event Action? AdminExitRequested;

    public string AdminExitHotkey { get; }
    public bool IsRunning => _isRunning;

    public GlobalHotkeyService()
    {
        AdminExitHotkey = ResolveAdminExitHotkey();
    }

    /// <summary>Start listening for the admin exit hotkey globally.</summary>
    public void Start()
    {
        if (_isRunning)
        {
            Logger.Warning("Global hotkey service already running");
            return;
        }

        _hookProc = HookCallback;
        var moduleHandle = GetModuleHandle(null);
        if (moduleHandle == IntPtr.Zero)
        {
            Logger.Error("Failed to get module handle for keyboard hook");
            return;
        }

        _hookHandle = SetWindowsHookEx(WH_KEYBOARD_LL, _hookProc, moduleHandle, 0);
        if (_hookHandle == IntPtr.Zero)
        {
            var err = Marshal.GetLastWin32Error();
            Logger.Error("Failed to install admin exit keyboard hook: Win32 error {Error}", err);
            return;
        }

        _isRunning = true;
        Logger.Information("Global hotkey service started — listening for {Hotkey} and Ctrl+Alt+Q", AdminExitHotkey);
    }

    /// <summary>Overload kept for backward compatibility; ignores hwnd.</summary>
    public void Start(IntPtr windowHandle) => Start();

    /// <summary>Stop and unregister the hook.</summary>
    public void Stop()
    {
        if (!_isRunning) return;

        if (_hookHandle != IntPtr.Zero)
        {
            UnhookWindowsHookEx(_hookHandle);
            _hookHandle = IntPtr.Zero;
        }
        _isRunning = false;
        Logger.Information("Global hotkey service stopped");
    }

    public void Dispose()
    {
        Stop();
        GC.SuppressFinalize(this);
    }

    // ==================== PRIVATE ====================

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0)
        {
            var msgType = wParam.ToInt32();
            if (msgType is WM_KEYDOWN or WM_SYSKEYDOWN)
            {
                var kb = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);
                var vk = (int)kb.vkCode;

                // Check if Ctrl+Alt are both held
                var ctrlPressed = (GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0;
                var altPressed = (GetAsyncKeyState(VK_MENU) & 0x8000) != 0;

                if (ctrlPressed && altPressed)
                {
                    // Primary: Ctrl+Alt+Space
                    // Legacy:  Ctrl+Alt+Q
                    if (vk == VK_SPACE || vk == VK_Q)
                    {
                        Logger.Information("Admin exit hotkey detected: Ctrl+Alt+{Key}", vk == VK_SPACE ? "Space" : "Q");
                        try
                        {
                            var handler = AdminExitRequested;
                            if (handler == null)
                            {
                                Logger.Warning("AdminExitRequested has no subscribers");
                            }
                            else
                            {
                                var app = System.Windows.Application.Current;
                                if (app == null)
                                {
                                    Logger.Warning("Application.Current is null — cannot dispatch");
                                }
                                else
                                {
                                    // Use Invoke (synchronous) instead of InvokeAsync to ensure
                                    // the handler runs immediately and we see any errors.
                                    app.Dispatcher.BeginInvoke(new Action(() =>
                                    {
                                        try
                                        {
                                            Logger.Information("Invoking AdminExitRequested handler");
                                            handler.Invoke();
                                        }
                                        catch (Exception innerEx)
                                        {
                                            Logger.Error(innerEx, "AdminExitRequested handler threw");
                                        }
                                    }));
                                }
                            }
                        }
                        catch (Exception ex)
                        {
                            Logger.Error(ex, "Error dispatching AdminExitRequested");
                        }
                        // Don't block the key — let it pass through
                    }
                }
            }
        }

        return CallNextHookEx(_hookHandle, nCode, wParam, lParam);
    }

    private static string ResolveAdminExitHotkey()
    {
        var registryValue = RegistryConfig.ReadValue("AdminExitHotkey");
        if (!string.IsNullOrEmpty(registryValue))
            return registryValue.Trim().ToLower().Replace(" ", "");

        var envValue = Environment.GetEnvironmentVariable("ADMIN_EXIT_HOTKEY");
        if (!string.IsNullOrEmpty(envValue))
            return envValue.Trim().ToLower().Replace(" ", "");

        return AppConstants.AdminExitHotkeyDefault;
    }
}
