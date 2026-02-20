using System.Windows;
using Serilog;
using SionyxKiosk.Views.Controls;
using SionyxKiosk.Views.Dialogs;

namespace SionyxKiosk.Services;

/// <summary>
/// Manages the lifecycle of system-level services: force logout, chat SSE,
/// keyboard/process restriction, operating hours, global hotkey, and print monitoring.
/// Extracted from App.xaml.cs to reduce god-class complexity.
/// </summary>
public class SystemServicesManager
{
    private static readonly ILogger Logger = Log.ForContext<SystemServicesManager>();

    private readonly ForceLogoutService _forceLogout;
    private readonly ChatService _chat;
    private readonly PrintMonitorService _printMonitor;
    private readonly OperatingHoursService _operatingHours;
    private readonly KeyboardRestrictionService _keyboard;
    private readonly ProcessRestrictionService _processRestriction;
    private readonly GlobalHotkeyService _globalHotkey;

    private Action<string>? _forceLogoutHandler;
    private Action? _adminExitHandler;

    public SystemServicesManager(
        ForceLogoutService forceLogout,
        ChatService chat,
        PrintMonitorService printMonitor,
        OperatingHoursService operatingHours,
        KeyboardRestrictionService keyboard,
        ProcessRestrictionService processRestriction,
        GlobalHotkeyService globalHotkey)
    {
        _forceLogout = forceLogout;
        _chat = chat;
        _printMonitor = printMonitor;
        _operatingHours = operatingHours;
        _keyboard = keyboard;
        _processRestriction = processRestriction;
        _globalHotkey = globalHotkey;
    }

    /// <summary>Raised when a force-logout is received from the server.</summary>
    public event Func<Task>? ForceLogoutReceived;

    /// <summary>Raised when the admin exit hotkey is pressed.</summary>
    public event Action? AdminExitRequested;

    /// <summary>
    /// Reinitialize user-scoped services and start all system services.
    /// </summary>
    public void Start(string userId, bool isKiosk)
    {
        if (string.IsNullOrEmpty(userId))
        {
            Logger.Warning("StartSystemServices called without a logged-in user");
            return;
        }

        _chat.Reinitialize(userId);
        _printMonitor.Reinitialize(userId);

        WireForceLogout(userId);
        _chat.StartListening();

        _ = Task.Run(async () =>
        {
            try { await _chat.CleanupOldMessagesAsync(); }
            catch (Exception ex) { Logger.Warning(ex, "Message cleanup failed (non-fatal)"); }
        });

        _ = _operatingHours.LoadSettingsAsync();

        if (isKiosk)
        {
            _processRestriction.Start();
            _keyboard.Start();
        }

        RewireAdminExitHandler();

        Logger.Information("System services started (kiosk={IsKiosk})", isKiosk);
    }

    /// <summary>
    /// Start the global hotkey listener with a basic admin-exit handler.
    /// Called once early (from auth window) so hotkey works at any app state.
    /// </summary>
    public void StartGlobalHotkey()
    {
        if (_globalHotkey.IsRunning) return;

        _adminExitHandler = () => AdminExitRequested?.Invoke();
        _globalHotkey.AdminExitRequested += _adminExitHandler;
        _globalHotkey.Start();
    }

    /// <summary>Stop all system services and unsubscribe event handlers.</summary>
    public async Task StopAsync(SessionService session)
    {
        try
        {
            if (_forceLogoutHandler != null)
            {
                _forceLogout.ForceLogout -= _forceLogoutHandler;
                _forceLogoutHandler = null;
            }

            RewireAdminExitHandler();

            _chat.StopListening();
            _forceLogout.StopListening();
            _operatingHours.StopMonitoring();
            _processRestriction.Stop();
            _keyboard.Stop();
            _printMonitor.StopMonitoring();

            if (session.IsActive)
                await session.EndSessionAsync("logout");
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error stopping system services");
        }
    }

    /// <summary>Stop all services for application shutdown (including hotkey).</summary>
    public void StopAll()
    {
        _processRestriction.Stop();
        _keyboard.Stop();
        _globalHotkey.Stop();
        _operatingHours.StopMonitoring();
        _forceLogout.StopListening();
        _chat.StopListening();
        _printMonitor.StopMonitoring();
    }

    private void WireForceLogout(string userId)
    {
        if (_forceLogoutHandler != null)
            _forceLogout.ForceLogout -= _forceLogoutHandler;

        _forceLogoutHandler = reason =>
        {
            Logger.Warning("Force logout received: {Reason}", reason);
            _ = Application.Current.Dispatcher.InvokeAsync(async () =>
            {
                if (ForceLogoutReceived != null)
                    await ForceLogoutReceived.Invoke();
            });
        };
        _forceLogout.ForceLogout += _forceLogoutHandler;
        _forceLogout.StartListening(userId);
    }

    private void RewireAdminExitHandler()
    {
        if (_adminExitHandler != null)
            _globalHotkey.AdminExitRequested -= _adminExitHandler;

        _adminExitHandler = () => AdminExitRequested?.Invoke();
        _globalHotkey.AdminExitRequested += _adminExitHandler;
    }
}
