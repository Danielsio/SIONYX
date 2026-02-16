using System.IO;
using System.Threading;
using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Serilog;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;
using SionyxKiosk.Views.Dialogs;
using SionyxKiosk.Views.Pages;
using SionyxKiosk.Views.Windows;

namespace SionyxKiosk;

/// <summary>
/// Application entry point. Sets up DI, Serilog, single-instance mutex,
/// and manages the Auth → Main window lifecycle.
/// </summary>
public partial class App : Application
{
    private static Mutex? _singleInstanceMutex;
    private IHost? _host;
    private bool _isKiosk;

    // Event handler references for proper unsubscription on singleton services.
    // Every delegate subscribed to a singleton event MUST be stored here so we
    // can reliably unsubscribe in StopSystemServicesAsync.
    private Action<string>? _forceLogoutHandler;
    private Action? _adminExitHandler;
    private Action? _sessionStartedHandler;
    private Action<int>? _sessionTimeUpdatedHandler;
    private Action<string>? _sessionEndedHandler;
    private Action? _warning5MinHandler;
    private Action? _warning1MinHandler;
    private Action<string>? _syncFailedHandler;
    private Action? _syncRestoredHandler;
    private Action<string, int, double, double>? _printJobAllowedHandler;
    private Action<string, int, double, double>? _printJobBlockedHandler;
    private Action<double>? _printBudgetUpdatedHandler;

    // Floating timer reference (managed across login cycles)
    private Views.Controls.FloatingTimer? _floatingTimer;

    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // ── Single-instance enforcement ──────────────────────────
        _singleInstanceMutex = new Mutex(true, "SionyxKiosk_SingleInstance", out bool isNew);
        if (!isNew)
        {
            MessageBox.Show("SIONYX כבר פועל.", "SIONYX", MessageBoxButton.OK, MessageBoxImage.Information);
            Shutdown();
            return;
        }

        // ── Serilog ──────────────────────────────────────────────
        var logDir = e.Args.Contains("--kiosk")
            ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SIONYX", "logs")
            : "logs";
        Directory.CreateDirectory(logDir);

        Log.Logger = new LoggerConfiguration()
            .MinimumLevel.Debug()
            .WriteTo.Console()
            .WriteTo.File(
                Path.Combine(logDir, "sionyx-.log"),
                rollingInterval: RollingInterval.Day,
                retainedFileCountLimit: 7,
                fileSizeLimitBytes: 10_000_000)
            .CreateLogger();

        Log.Information("SIONYX Kiosk WPF starting, version {Version}", GetVersion());

        // ── Global exception handlers ────────────────────────────
        DispatcherUnhandledException += (_, ex) =>
        {
            Log.Fatal(ex.Exception, "Unhandled UI exception");
            WriteCrashLog(ex.Exception, logDir);
            ex.Handled = true;
        };
        AppDomain.CurrentDomain.UnhandledException += (_, ex) =>
        {
            var exception = ex.ExceptionObject as Exception;
            Log.Fatal(exception, "Unhandled domain exception");
            WriteCrashLog(exception, logDir);
        };
        TaskScheduler.UnobservedTaskException += (_, ex) =>
        {
            Log.Error(ex.Exception, "Unobserved task exception");
            ex.SetObserved();
        };

        // ── Host + DI Container ──────────────────────────────────
        _host = Host.CreateDefaultBuilder()
            .UseSerilog()
            .ConfigureServices((_, services) =>
            {
                // Infrastructure
                services.AddSingleton(_ => FirebaseConfig.Load());
                services.AddSingleton(sp => new FirebaseClient(sp.GetRequiredService<FirebaseConfig>()));
                services.AddSingleton(_ => new LocalDatabase());

                // Business Services (singleton - no user-specific params)
                services.AddSingleton(sp => new AuthService(
                    sp.GetRequiredService<FirebaseClient>(),
                    sp.GetRequiredService<LocalDatabase>()));
                services.AddSingleton(sp => new ComputerService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new PackageService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new PurchaseService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new OrganizationMetadataService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new OperatingHoursService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new ForceLogoutService(sp.GetRequiredService<FirebaseClient>()));

                // User-scoped services (singleton, but Reinitialize is called after each login)
                services.AddSingleton(sp =>
                {
                    var fb = sp.GetRequiredService<FirebaseClient>();
                    var cfg = sp.GetRequiredService<FirebaseConfig>();
                    return new SessionService(fb, "", cfg.OrgId);
                });
                services.AddSingleton(sp =>
                {
                    var fb = sp.GetRequiredService<FirebaseClient>();
                    return new ChatService(fb, "");
                });
                services.AddSingleton(sp =>
                {
                    var fb = sp.GetRequiredService<FirebaseClient>();
                    return new PrintMonitorService(fb, "");
                });

                // System Services
                services.AddSingleton(_ => new KeyboardRestrictionService());
                services.AddSingleton(_ => new GlobalHotkeyService());
                services.AddSingleton(_ => new ProcessRestrictionService());
                services.AddSingleton(_ => new ProcessCleanupService());
                services.AddSingleton(_ => new BrowserCleanupService());

                // ViewModels
                services.AddTransient<AuthViewModel>(sp => new AuthViewModel(
                    sp.GetRequiredService<AuthService>(),
                    sp.GetRequiredService<OrganizationMetadataService>()));
                services.AddTransient<MainViewModel>();
                services.AddTransient<HomeViewModel>(sp =>
                {
                    var session = sp.GetRequiredService<SessionService>();
                    var chat = sp.GetRequiredService<ChatService>();
                    var hours = sp.GetRequiredService<OperatingHoursService>();
                    var auth = sp.GetRequiredService<AuthService>();
                    return new HomeViewModel(session, chat, hours, auth.CurrentUser!);
                });
                services.AddTransient<PackagesViewModel>(sp =>
                {
                    var pkg = sp.GetRequiredService<PackageService>();
                    var purchase = sp.GetRequiredService<PurchaseService>();
                    var auth = sp.GetRequiredService<AuthService>();
                    return new PackagesViewModel(pkg, purchase, auth.CurrentUser?.Uid ?? "");
                });
                services.AddTransient<HistoryViewModel>(sp =>
                {
                    var purchase = sp.GetRequiredService<PurchaseService>();
                    var auth = sp.GetRequiredService<AuthService>();
                    return new HistoryViewModel(purchase, auth.CurrentUser?.Uid ?? "");
                });
                services.AddTransient(sp => new HelpViewModel(sp.GetRequiredService<OrganizationMetadataService>()));
                services.AddTransient<PaymentViewModel>(sp =>
                {
                    var purchase = sp.GetRequiredService<PurchaseService>();
                    var auth = sp.GetRequiredService<AuthService>();
                    return new PaymentViewModel(purchase, auth.CurrentUser?.Uid ?? "");
                });
                services.AddTransient(sp => new MessageViewModel(sp.GetRequiredService<ChatService>()));

                // Views
                services.AddTransient<AuthWindow>();
                services.AddTransient<MainWindow>(sp =>
                {
                    var vm = sp.GetRequiredService<MainViewModel>();
                    return new MainWindow(vm, sp);
                });
                services.AddTransient<HomePage>(sp =>
                {
                    var vm = sp.GetRequiredService<HomeViewModel>();
                    return new HomePage(vm, sp);
                });
                services.AddTransient<PackagesPage>(sp =>
                {
                    var vm = sp.GetRequiredService<PackagesViewModel>();
                    return new PackagesPage(vm, sp);
                });
                services.AddTransient<HistoryPage>();
                services.AddTransient<HelpPage>();
            })
            .Build();

        await _host.StartAsync();

        // ── Start with Auth or Main ──────────────────────────────
        _isKiosk = e.Args.Contains("--kiosk");
        var isVerbose = e.Args.Contains("--verbose");

        if (isVerbose)
            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Verbose()
                .WriteTo.Console()
                .WriteTo.File("logs/sionyx-.log", rollingInterval: RollingInterval.Day)
                .CreateLogger();

        ShowAuthWindow();
    }

    // ================================================================
    // Window Lifecycle
    // ================================================================

    private void ShowAuthWindow()
    {
        var authVm = _host!.Services.GetRequiredService<AuthViewModel>();

        // AuthViewModel is Transient (new instance each time) so event subscriptions
        // are fresh and don't leak.
        authVm.LoginSucceeded += OnLoginSucceeded;
        authVm.RegistrationSucceeded += OnLoginSucceeded;

        var authWindow = new AuthWindow(authVm);
        authWindow.Show();
        MainWindow = authWindow;

        _ = TryAutoLoginAsync(authVm);
    }

    private void OnLoginSucceeded()
    {
        Current.Dispatcher.Invoke(() =>
        {
            if (MainWindow is AuthWindow aw)
            {
                aw.AllowClose();
                aw.Close();
            }
            ShowMainWindow();
        });
    }

    private async Task TryAutoLoginAsync(AuthViewModel authVm)
    {
        var auth = _host!.Services.GetRequiredService<AuthService>();
        var isLoggedIn = await auth.IsLoggedInAsync();
        if (isLoggedIn)
        {
            authVm.TriggerAutoLogin();
        }
    }

    private void ShowMainWindow()
    {
        var mainWindow = _host!.Services.GetRequiredService<MainWindow>();
        var mainVm = (MainViewModel)mainWindow.DataContext;

        mainVm.LogoutRequested += OnLogoutRequested;

        // Always fullscreen, topmost (kiosk behavior)
        mainWindow.WindowState = WindowState.Maximized;
        mainWindow.Topmost = true;

        // Show window and set as MainWindow BEFORE starting services
        // (services need the window handle for global hotkeys)
        mainWindow.Show();
        MainWindow = mainWindow;

        // Start system services
        StartSystemServices();
    }

    private void OnLogoutRequested()
    {
        _ = Current.Dispatcher.InvokeAsync(async () =>
        {
            try
            {
                await StopSystemServicesAsync();

                var auth = _host!.Services.GetRequiredService<AuthService>();
                await auth.LogoutAsync();

                if (MainWindow is Views.Windows.MainWindow mw)
                {
                    mw.AllowClose();
                    mw.Close();
                }
                ShowAuthWindow();
            }
            catch (Exception ex)
            {
                Log.Error(ex, "Error during logout");
            }
        });
    }

    // ================================================================
    // System Services Lifecycle
    // ================================================================

    private void StartSystemServices()
    {
        try
        {
            var auth = _host!.Services.GetRequiredService<AuthService>();
            var userId = auth.CurrentUser?.Uid ?? "";

            if (string.IsNullOrEmpty(userId))
            {
                Log.Warning("StartSystemServices called without a logged-in user");
                return;
            }

            // ── Reinitialize user-scoped singletons with current userId ──
            var session = _host.Services.GetRequiredService<SessionService>();
            var chat = _host.Services.GetRequiredService<ChatService>();
            var printMonitor = _host.Services.GetRequiredService<PrintMonitorService>();

            session.Reinitialize(userId);
            chat.Reinitialize(userId);
            printMonitor.Reinitialize(userId);

            // ── Force logout listener ──
            var forceLogout = _host.Services.GetRequiredService<ForceLogoutService>();
            if (_forceLogoutHandler != null)
                forceLogout.ForceLogout -= _forceLogoutHandler;

            _forceLogoutHandler = reason =>
            {
                Log.Warning("Force logout received: {Reason}", reason);
                _ = Current.Dispatcher.InvokeAsync(async () =>
                {
                    try
                    {
                        // Notify the user before logging them out
                        AlertDialog.Show(
                            "ניתוק על ידי מנהל",
                            "הותנקת מהמערכת על ידי מנהל. אנא התחבר מחדש.",
                            AlertDialog.AlertType.Warning,
                            MainWindow);

                        await StopSystemServicesAsync();
                        await auth.LogoutAsync();
                        if (MainWindow is Views.Windows.MainWindow mw)
                        {
                            mw.AllowClose();
                            mw.Close();
                        }
                        ShowAuthWindow();
                    }
                    catch (Exception ex)
                    {
                        Log.Error(ex, "Error during force logout");
                    }
                });
            };
            forceLogout.ForceLogout += _forceLogoutHandler;
            forceLogout.StartListening(userId);

            // ── Chat service SSE listener ──
            chat.StartListening();

            // ── Session lifecycle events ──
            UnsubscribeSessionEvents(session);
            SubscribeSessionEvents(session, printMonitor);

            // ── Print monitor events ──
            UnsubscribePrintMonitorEvents(printMonitor);
            SubscribePrintMonitorEvents(printMonitor);

            // ── Operating hours monitoring ──
            var hours = _host.Services.GetRequiredService<OperatingHoursService>();
            _ = hours.LoadSettingsAsync();
            // Note: per-session monitoring is started by SessionService.StartSessionAsync

            // ── Process restriction (always in kiosk mode) ──
            if (_isKiosk)
            {
                var procRestrict = _host.Services.GetRequiredService<ProcessRestrictionService>();
                procRestrict.Start();

                var keyboard = _host.Services.GetRequiredService<KeyboardRestrictionService>();
                keyboard.Start();
            }

            // ── Global hotkey (admin exit) ──
            if (MainWindow != null)
            {
                var hwnd = new System.Windows.Interop.WindowInteropHelper(MainWindow).Handle;
                if (hwnd != IntPtr.Zero)
                {
                    var hotkey = _host.Services.GetRequiredService<GlobalHotkeyService>();
                    if (_adminExitHandler != null)
                        hotkey.AdminExitRequested -= _adminExitHandler;

                    _adminExitHandler = () =>
                    {
                        Current.Dispatcher.Invoke(() => ShowAdminExitDialog(auth));
                    };
                    hotkey.AdminExitRequested += _adminExitHandler;
                    hotkey.Start(hwnd);
                }
            }

            Log.Information("System services started successfully (kiosk={IsKiosk})", _isKiosk);
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error starting system services");
        }
    }

    // ── Session event wiring ─────────────────────────────────────

    private void SubscribeSessionEvents(SessionService session, PrintMonitorService printMonitor)
    {
        _sessionStartedHandler = () =>
        {
            printMonitor.StartMonitoring();
            Current.Dispatcher.Invoke(() =>
            {
                // Create and show floating timer
                _floatingTimer = new Views.Controls.FloatingTimer();
                _floatingTimer.UpdatePrintBalance(
                    _host?.Services.GetService<AuthService>()?.CurrentUser?.PrintBalance ?? 0);
                _floatingTimer.ReturnRequested += OnFloatingTimerReturn;
                _floatingTimer.Show();

                // Minimize main window — the user works at their desktop with the timer overlay
                if (MainWindow is Views.Windows.MainWindow mw)
                {
                    mw.Topmost = false;
                    mw.WindowState = WindowState.Minimized;
                }
            });
        };

        _sessionTimeUpdatedHandler = remaining =>
        {
            Current.Dispatcher.Invoke(() =>
            {
                _floatingTimer?.UpdateTime(remaining);
                _floatingTimer?.UpdateUsageTime(session.TimeUsed);
            });
        };

        _sessionEndedHandler = reason =>
        {
            printMonitor.StopMonitoring();
            Current.Dispatcher.Invoke(() =>
            {
                // Close floating timer
                if (_floatingTimer != null)
                {
                    _floatingTimer.ReturnRequested -= OnFloatingTimerReturn;
                    _floatingTimer.Close();
                    _floatingTimer = null;
                }

                // Restore main window
                if (MainWindow is Views.Windows.MainWindow mw)
                {
                    mw.WindowState = WindowState.Maximized;
                    mw.Topmost = true;
                    mw.Activate();
                    mw.NavigateHome();
                }
            });
        };

        _warning5MinHandler = () =>
        {
            Log.Information("Session warning: 5 minutes remaining");
            Current.Dispatcher.Invoke(() =>
            {
                if (MainWindow is Views.Windows.MainWindow mw)
                    mw.ShowToast("5 דקות נותרו", "ההפעלה תסתיים בעוד 5 דקות",
                        Views.Controls.ToastNotification.ToastType.Warning, 5000);
            });
        };

        _warning1MinHandler = () =>
        {
            Log.Information("Session warning: 1 minute remaining");
            Current.Dispatcher.Invoke(() =>
            {
                if (MainWindow is Views.Windows.MainWindow mw)
                    mw.ShowToast("דקה אחרונה!", "ההפעלה תסתיים בעוד דקה",
                        Views.Controls.ToastNotification.ToastType.Error, 5000);
            });
        };

        _syncFailedHandler = msg =>
        {
            Current.Dispatcher.Invoke(() => _floatingTimer?.SetOfflineMode(true));
        };

        _syncRestoredHandler = () =>
        {
            Current.Dispatcher.Invoke(() => _floatingTimer?.SetOfflineMode(false));
        };

        session.SessionStarted += _sessionStartedHandler;
        session.TimeUpdated += _sessionTimeUpdatedHandler;
        session.SessionEnded += _sessionEndedHandler;
        session.Warning5Min += _warning5MinHandler;
        session.Warning1Min += _warning1MinHandler;
        session.SyncFailed += _syncFailedHandler;
        session.SyncRestored += _syncRestoredHandler;
    }

    private void UnsubscribeSessionEvents(SessionService session)
    {
        if (_sessionStartedHandler != null) session.SessionStarted -= _sessionStartedHandler;
        if (_sessionTimeUpdatedHandler != null) session.TimeUpdated -= _sessionTimeUpdatedHandler;
        if (_sessionEndedHandler != null) session.SessionEnded -= _sessionEndedHandler;
        if (_warning5MinHandler != null) session.Warning5Min -= _warning5MinHandler;
        if (_warning1MinHandler != null) session.Warning1Min -= _warning1MinHandler;
        if (_syncFailedHandler != null) session.SyncFailed -= _syncFailedHandler;
        if (_syncRestoredHandler != null) session.SyncRestored -= _syncRestoredHandler;

        _sessionStartedHandler = null;
        _sessionTimeUpdatedHandler = null;
        _sessionEndedHandler = null;
        _warning5MinHandler = null;
        _warning1MinHandler = null;
        _syncFailedHandler = null;
        _syncRestoredHandler = null;
    }

    // ── Print monitor event wiring ──────────────────────────────

    private void SubscribePrintMonitorEvents(PrintMonitorService printMonitor)
    {
        _printJobAllowedHandler = (doc, pages, cost, remaining) =>
        {
            Log.Information("Print job allowed: '{Doc}' ({Pages}p, {Cost}₪)", doc, pages, cost);
            Current.Dispatcher.Invoke(() =>
            {
                _floatingTimer?.UpdatePrintBalance(remaining);
                if (MainWindow is Views.Windows.MainWindow mw)
                    mw.ShowToast("הדפסה אושרה", $"{doc} — {cost:F2}₪",
                        Views.Controls.ToastNotification.ToastType.Success);
            });
        };

        _printJobBlockedHandler = (doc, pages, cost, budget) =>
        {
            Log.Warning("Print job blocked: '{Doc}' ({Pages}p, {Cost}₪, budget={Budget}₪)", doc, pages, cost, budget);
            Current.Dispatcher.Invoke(() =>
            {
                if (MainWindow is Views.Windows.MainWindow mw)
                    mw.ShowToast("הדפסה נדחתה", $"יתרה לא מספיקה ({budget:F2}₪ זמין, צריך {cost:F2}₪)",
                        Views.Controls.ToastNotification.ToastType.Error, 5000);
            });
        };

        _printBudgetUpdatedHandler = budget =>
        {
            Current.Dispatcher.Invoke(() => _floatingTimer?.UpdatePrintBalance(budget));
        };

        printMonitor.JobAllowed += _printJobAllowedHandler;
        printMonitor.JobBlocked += _printJobBlockedHandler;
        printMonitor.BudgetUpdated += _printBudgetUpdatedHandler;
    }

    private void UnsubscribePrintMonitorEvents(PrintMonitorService printMonitor)
    {
        if (_printJobAllowedHandler != null) printMonitor.JobAllowed -= _printJobAllowedHandler;
        if (_printJobBlockedHandler != null) printMonitor.JobBlocked -= _printJobBlockedHandler;
        if (_printBudgetUpdatedHandler != null) printMonitor.BudgetUpdated -= _printBudgetUpdatedHandler;

        _printJobAllowedHandler = null;
        _printJobBlockedHandler = null;
        _printBudgetUpdatedHandler = null;
    }

    // ── FloatingTimer return button ─────────────────────────────

    private void OnFloatingTimerReturn()
    {
        // End session — this triggers SessionEnded which handles closing the timer
        // and restoring the main window (see _sessionEndedHandler above).
        var session = _host?.Services.GetService<SessionService>();
        if (session?.IsActive == true)
            _ = session.EndSessionAsync("user");
    }

    // ── Service teardown ────────────────────────────────────────

    private async Task StopSystemServicesAsync()
    {
        try
        {
            // ── Unsubscribe all singleton event handlers ──
            var forceLogout = _host?.Services.GetService<ForceLogoutService>();
            if (forceLogout != null && _forceLogoutHandler != null)
            {
                forceLogout.ForceLogout -= _forceLogoutHandler;
                _forceLogoutHandler = null;
            }

            var hotkey = _host?.Services.GetService<GlobalHotkeyService>();
            if (hotkey != null && _adminExitHandler != null)
            {
                hotkey.AdminExitRequested -= _adminExitHandler;
                _adminExitHandler = null;
            }

            var session = _host?.Services.GetService<SessionService>();
            if (session != null)
                UnsubscribeSessionEvents(session);

            var printMonitor = _host?.Services.GetService<PrintMonitorService>();
            if (printMonitor != null)
                UnsubscribePrintMonitorEvents(printMonitor);

            // ── Stop services ──
            _host?.Services.GetService<ChatService>()?.StopListening();
            forceLogout?.StopListening();
            _host?.Services.GetService<OperatingHoursService>()?.StopMonitoring();
            _host?.Services.GetService<ProcessRestrictionService>()?.Stop();
            _host?.Services.GetService<KeyboardRestrictionService>()?.Stop();
            hotkey?.Stop();
            printMonitor?.StopMonitoring();

            if (session?.IsActive == true)
                await session.EndSessionAsync("logout");

            // Close floating timer
            Current.Dispatcher.Invoke(() =>
            {
                if (_floatingTimer != null)
                {
                    _floatingTimer.ReturnRequested -= OnFloatingTimerReturn;
                    _floatingTimer.Close();
                    _floatingTimer = null;
                }
            });
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error stopping system services");
        }
    }

    // ================================================================
    // Admin Exit
    // ================================================================

    private void ShowAdminExitDialog(AuthService auth)
    {
        var dialog = new Views.Dialogs.AdminExitDialog();
        dialog.Owner = MainWindow;
        if (dialog.ShowDialog() == true)
        {
            var password = dialog.EnteredPassword;
            if (password == Infrastructure.AppConstants.GetAdminExitPassword())
            {
                Log.Information("Admin exit: correct password, shutting down");
                _ = Task.Run(async () =>
                {
                    await StopSystemServicesAsync();
                    await auth.LogoutAsync();
                    Current.Dispatcher.Invoke(() =>
                    {
                        if (MainWindow is Views.Windows.MainWindow mw)
                            mw.AllowClose();
                        else if (MainWindow is AuthWindow aw)
                            aw.AllowClose();
                        Shutdown();
                    });
                });
            }
            else
            {
                Log.Warning("Admin exit: incorrect password");
                MessageBox.Show("סיסמה שגויה", "SIONYX", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }
    }

    // ================================================================
    // Application Exit
    // ================================================================

    protected override async void OnExit(ExitEventArgs e)
    {
        Log.Information("SIONYX Kiosk shutting down");

        try
        {
            // Stop system services
            _host?.Services.GetService<ProcessRestrictionService>()?.Stop();
            _host?.Services.GetService<KeyboardRestrictionService>()?.Stop();
            _host?.Services.GetService<GlobalHotkeyService>()?.Stop();
            _host?.Services.GetService<OperatingHoursService>()?.StopMonitoring();
            _host?.Services.GetService<ForceLogoutService>()?.StopListening();
            _host?.Services.GetService<ChatService>()?.StopListening();
            _host?.Services.GetService<PrintMonitorService>()?.StopMonitoring();

            // Allow any open window to close during shutdown
            if (MainWindow is Views.Windows.MainWindow mw) mw.AllowClose();
            else if (MainWindow is AuthWindow aw) aw.AllowClose();

            if (_host != null) await _host.StopAsync();
            _host?.Dispose();
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error during shutdown");
        }
        finally
        {
            _singleInstanceMutex?.ReleaseMutex();
            _singleInstanceMutex?.Dispose();
            Log.CloseAndFlush();
        }

        base.OnExit(e);
    }

    // ================================================================
    // Helpers
    // ================================================================

    private static string GetVersion() => "1.0.0";

    private static void WriteCrashLog(Exception? ex, string logDir)
    {
        try
        {
            var crashFile = Path.Combine(logDir, $"crash_{DateTime.Now:yyyyMMdd_HHmmss}.log");
            var content = $"""
                SIONYX Kiosk Crash Report
                Time: {DateTime.Now:O}
                Machine: {Environment.MachineName}
                OS: {Environment.OSVersion}
                
                Exception:
                {ex}
                """;
            File.WriteAllText(crashFile, content);
        }
        catch
        {
            // Best-effort crash log
        }
    }
}
