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

    private SystemServicesManager? _systemServices;
    private SessionCoordinator? _sessionCoordinator;

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
                services.AddSingleton(sp => new ComputerService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new AuthService(
                    sp.GetRequiredService<FirebaseClient>(),
                    sp.GetRequiredService<LocalDatabase>(),
                    sp.GetRequiredService<ComputerService>()));
                services.AddSingleton(sp => new PackageService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new PurchaseService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new OrganizationMetadataService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new OperatingHoursService(sp.GetRequiredService<FirebaseClient>()));
                services.AddSingleton(sp => new ForceLogoutService(sp.GetRequiredService<FirebaseClient>()));

                // System Services
                services.AddSingleton(_ => new ProcessCleanupService());
                services.AddSingleton(_ => new BrowserCleanupService());

                // User-scoped services (singleton, but Reinitialize is called after each login)
                services.AddSingleton(sp =>
                {
                    var fb = sp.GetRequiredService<FirebaseClient>();
                    var cfg = sp.GetRequiredService<FirebaseConfig>();
                    return new SessionService(fb, "", cfg.OrgId,
                        sp.GetRequiredService<ComputerService>(),
                        sp.GetRequiredService<OperatingHoursService>(),
                        sp.GetRequiredService<ProcessCleanupService>(),
                        sp.GetRequiredService<BrowserCleanupService>());
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

                services.AddSingleton(_ => new KeyboardRestrictionService());
                services.AddSingleton(_ => new GlobalHotkeyService());
                services.AddSingleton(_ => new ProcessRestrictionService());

                // Factories
                services.AddSingleton<IPaymentDialogFactory>(sp => new PaymentDialogFactory(
                    sp.GetRequiredService<PurchaseService>(),
                    sp.GetRequiredService<OrganizationMetadataService>(),
                    sp.GetRequiredService<FirebaseClient>(),
                    sp.GetRequiredService<AuthService>()));

                // Coordinators
                services.AddSingleton(sp => new SystemServicesManager(
                    sp.GetRequiredService<ForceLogoutService>(),
                    sp.GetRequiredService<ChatService>(),
                    sp.GetRequiredService<PrintMonitorService>(),
                    sp.GetRequiredService<OperatingHoursService>(),
                    sp.GetRequiredService<KeyboardRestrictionService>(),
                    sp.GetRequiredService<ProcessRestrictionService>(),
                    sp.GetRequiredService<GlobalHotkeyService>()));
                services.AddSingleton(sp => new SessionCoordinator(
                    sp.GetRequiredService<SessionService>(),
                    sp.GetRequiredService<PrintMonitorService>(),
                    sp.GetRequiredService<AuthService>()));

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
                    return new PackagesPage(vm, sp.GetRequiredService<IPaymentDialogFactory>());
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

        _systemServices = _host!.Services.GetRequiredService<SystemServicesManager>();
        _sessionCoordinator = _host!.Services.GetRequiredService<SessionCoordinator>();

        _systemServices.AdminExitRequested += () =>
        {
            Current.Dispatcher.Invoke(() =>
            {
                var auth = _host?.Services.GetService<AuthService>();
                if (auth != null) ShowAdminExitDialog(auth);
            });
        };

        _systemServices.ForceLogoutReceived += async () =>
        {
            AlertDialog.Show("ניתוק על ידי מנהל",
                "הותנקת מהמערכת על ידי מנהל. אנא התחבר מחדש.",
                AlertDialog.AlertType.Warning, MainWindow);
            await StopSystemServicesAsync();
            var auth = _host!.Services.GetRequiredService<AuthService>();
            await auth.LogoutAsync();
            if (MainWindow is Views.Windows.MainWindow mw) { mw.AllowClose(); mw.Close(); }
            ShowAuthWindow();
        };

        _sessionCoordinator.MinimizeMainWindow += () =>
        {
            if (MainWindow is Views.Windows.MainWindow mw)
            {
                mw.Topmost = false;
                mw.WindowState = WindowState.Minimized;
            }
        };
        _sessionCoordinator.RestoreMainWindow += () =>
        {
            if (MainWindow is Views.Windows.MainWindow mw)
            {
                mw.WindowState = WindowState.Maximized;
                mw.Topmost = true;
                mw.Activate();
                mw.NavigateHome();
            }
        };

        _systemServices.StartGlobalHotkey();

        _ = TryAutoLoginAsync(authVm);
    }

    private void OnLoginSucceeded()
    {
        Current.Dispatcher.Invoke(() =>
        {
            try
            {
                Log.Information("Login succeeded — closing auth window, opening main window");

                if (MainWindow is AuthWindow aw)
                {
                    aw.AllowClose();
                    aw.Close();
                }
                ShowMainWindow();
            }
            catch (Exception ex)
            {
                Log.Fatal(ex, "Failed to transition from auth to main window");
                // Re-show the auth window so the user isn't stuck with an invisible app
                try { ShowAuthWindow(); }
                catch (Exception ex2) { Log.Fatal(ex2, "Recovery failed — app is in a broken state"); }
            }
        });
    }

    private async Task TryAutoLoginAsync(AuthViewModel authVm)
    {
        try
        {
            var auth = _host!.Services.GetRequiredService<AuthService>();
            var isLoggedIn = await auth.IsLoggedInAsync();
            if (isLoggedIn)
            {
                Log.Information("Auto-login succeeded, transitioning to main window");
                authVm.TriggerAutoLogin();
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Auto-login failed — staying on auth window");
        }
    }

    private void ShowMainWindow()
    {
        Log.Debug("Creating MainWindow from DI");
        var mainWindow = _host!.Services.GetRequiredService<MainWindow>();
        var mainVm = (MainViewModel)mainWindow.DataContext;

        mainVm.LogoutRequested += OnLogoutRequested;

        // Always fullscreen, topmost (kiosk behavior)
        mainWindow.WindowState = WindowState.Maximized;
        mainWindow.Topmost = true;

        mainWindow.Show();
        MainWindow = mainWindow;
        Log.Information("MainWindow shown and set as Application.MainWindow");

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

            var session = _host.Services.GetRequiredService<SessionService>();
            session.Reinitialize(userId);

            _sessionCoordinator!.Subscribe();
            _systemServices!.Start(userId, _isKiosk);

            Log.Information("System services started successfully (kiosk={IsKiosk})", _isKiosk);
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error starting system services");
        }
    }

    /// <summary>Called from the HomePage when the user wants to return to the active session.</summary>
    public void ResumeSession()
    {
        _sessionCoordinator?.ResumeSession();
    }

    private async Task StopSystemServicesAsync()
    {
        try
        {
            _sessionCoordinator?.Unsubscribe();
            _sessionCoordinator?.CloseFloatingTimer();

            var session = _host?.Services.GetService<SessionService>();
            if (session != null)
                await _systemServices!.StopAsync(session);
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
        try
        {
            // If MainWindow is minimized (during a session), restore it first so
            // the dialog is visible.  We also need to make the dialog Topmost to
            // guarantee it appears above everything including the FloatingTimer.
            var dialog = new Views.Dialogs.AdminExitDialog();

            if (MainWindow is Views.Windows.MainWindow mw && mw.WindowState == WindowState.Minimized)
            {
                // During an active session the main window is minimized.
                // Don't set Owner (modal to a minimized window is invisible on
                // some Windows versions). Instead just show Topmost.
                dialog.Owner = null;
                dialog.WindowStartupLocation = WindowStartupLocation.CenterScreen;
                dialog.Topmost = true;
            }
            else
            {
                dialog.Owner = MainWindow;
            }

            Log.Information("Showing admin exit dialog");

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
                            if (MainWindow is Views.Windows.MainWindow mainWin)
                                mainWin.AllowClose();
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
        catch (Exception ex)
        {
            Log.Error(ex, "Error showing admin exit dialog");
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
            _systemServices?.StopAll();

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
