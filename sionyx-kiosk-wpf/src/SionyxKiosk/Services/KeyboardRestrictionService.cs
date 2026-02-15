using System.Runtime.InteropServices;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Blocks dangerous system keys (Alt+Tab, Alt+F4, Windows key, etc.)
/// using a low-level keyboard hook via SetWindowsHookEx.
/// </summary>
public class KeyboardRestrictionService : IDisposable
{
    private static readonly ILogger Logger = Log.ForContext<KeyboardRestrictionService>();

    // Win32 constants
    private const int WH_KEYBOARD_LL = 13;
    private const int WM_KEYDOWN = 0x0100;
    private const int WM_SYSKEYDOWN = 0x0104;
    private const int VK_TAB = 0x09;
    private const int VK_ESCAPE = 0x1B;
    private const int VK_F4 = 0x73;
    private const int VK_LWIN = 0x5B;
    private const int VK_RWIN = 0x5C;
    private const int VK_MENU = 0x12;    // Alt
    private const int VK_CONTROL = 0x11; // Ctrl
    private const int VK_SHIFT = 0x10;   // Shift

    // P/Invoke
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

    [StructLayout(LayoutKind.Sequential)]
    private struct KBDLLHOOKSTRUCT
    {
        public uint vkCode;
        public uint scanCode;
        public uint flags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    // State
    private IntPtr _hookHandle = IntPtr.Zero;
    private LowLevelKeyboardProc? _hookProc; // prevent GC
    private Thread? _hookThread;

    public bool Enabled { get; set; }
    public bool IsActive => _hookHandle != IntPtr.Zero && Enabled;

    // Blocked combos
    private readonly Dictionary<string, bool> _blockedCombos = new()
    {
        ["alt+tab"] = true,
        ["alt+f4"] = true,
        ["alt+esc"] = true,
        ["win"] = true,
        ["ctrl+shift+esc"] = true,
        ["ctrl+esc"] = true,
    };

    // Events
    public event Action<string>? BlockedKeyPressed;

    public KeyboardRestrictionService(bool enabled = true)
    {
        Enabled = enabled;
    }

    public void Start()
    {
        if (!Enabled)
        {
            Logger.Information("Keyboard restriction disabled");
            return;
        }
        if (_hookHandle != IntPtr.Zero)
        {
            Logger.Warning("Keyboard hook already installed");
            return;
        }

        Logger.Information("Starting keyboard restriction service");
        _hookThread = new Thread(RunHookLoop) { IsBackground = true, Name = "KeyboardHook" };
        _hookThread.Start();
    }

    public void Stop()
    {
        if (_hookHandle != IntPtr.Zero)
        {
            Logger.Information("Stopping keyboard restriction service");
            UnhookWindowsHookEx(_hookHandle);
            _hookHandle = IntPtr.Zero;
        }
    }

    public void Dispose()
    {
        Stop();
        GC.SuppressFinalize(this);
    }

    // ==================== PRIVATE ====================

    private void RunHookLoop()
    {
        try
        {
            _hookProc = HookCallback;
            var moduleHandle = GetModuleHandle(null);
            if (moduleHandle == IntPtr.Zero)
            {
                Logger.Error("Failed to get module handle");
                return;
            }

            _hookHandle = SetWindowsHookEx(WH_KEYBOARD_LL, _hookProc, moduleHandle, 0);
            if (_hookHandle == IntPtr.Zero)
            {
                Logger.Error("Failed to install keyboard hook: error {Error}", Marshal.GetLastWin32Error());
                return;
            }

            Logger.Information("Keyboard restriction hook installed");

            // Run message loop (required for low-level hooks)
            MSG msg;
            while (GetMessage(out msg, IntPtr.Zero, 0, 0) != 0)
            {
                TranslateMessage(ref msg);
                DispatchMessage(ref msg);
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error in keyboard hook thread");
        }
        finally
        {
            if (_hookHandle != IntPtr.Zero)
            {
                UnhookWindowsHookEx(_hookHandle);
                _hookHandle = IntPtr.Zero;
            }
        }
    }

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0 && Enabled)
        {
            var kb = Marshal.PtrToStructure<KBDLLHOOKSTRUCT>(lParam);
            var vk = (int)kb.vkCode;

            var altPressed = (GetAsyncKeyState(VK_MENU) & 0x8000) != 0;
            var ctrlPressed = (GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0;
            var shiftPressed = (GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0;

            string? comboName = null;

            if (vk is VK_LWIN or VK_RWIN && _blockedCombos.GetValueOrDefault("win"))
                comboName = "Windows key";
            else if (vk == VK_TAB && altPressed && _blockedCombos.GetValueOrDefault("alt+tab"))
                comboName = "Alt+Tab";
            else if (vk == VK_F4 && altPressed && _blockedCombos.GetValueOrDefault("alt+f4"))
                comboName = "Alt+F4";
            else if (vk == VK_ESCAPE && altPressed && _blockedCombos.GetValueOrDefault("alt+esc"))
                comboName = "Alt+Escape";
            else if (vk == VK_ESCAPE && ctrlPressed && shiftPressed && _blockedCombos.GetValueOrDefault("ctrl+shift+esc"))
                comboName = "Ctrl+Shift+Escape";
            else if (vk == VK_ESCAPE && ctrlPressed && !shiftPressed && _blockedCombos.GetValueOrDefault("ctrl+esc"))
                comboName = "Ctrl+Escape";

            if (comboName != null)
            {
                Logger.Debug("Blocked: {Combo}", comboName);
                try { BlockedKeyPressed?.Invoke(comboName); } catch { /* Don't crash hook */ }
                return (IntPtr)1; // Block
            }
        }

        return CallNextHookEx(_hookHandle, nCode, wParam, lParam);
    }

    // Message loop P/Invoke
    [StructLayout(LayoutKind.Sequential)]
    private struct MSG
    {
        public IntPtr hwnd;
        public uint message;
        public IntPtr wParam;
        public IntPtr lParam;
        public uint time;
        public POINT pt;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct POINT { public int x; public int y; }

    [DllImport("user32.dll")]
    private static extern int GetMessage(out MSG lpMsg, IntPtr hWnd, uint wMsgFilterMin, uint wMsgFilterMax);

    [DllImport("user32.dll")]
    private static extern bool TranslateMessage(ref MSG lpMsg);

    [DllImport("user32.dll")]
    private static extern IntPtr DispatchMessage(ref MSG lpMsg);
}
