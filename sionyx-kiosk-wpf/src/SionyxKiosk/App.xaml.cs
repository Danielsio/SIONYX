using System.Threading;
using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Serilog;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;
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
        Log.Logger = new LoggerConfiguration()
            .MinimumLevel.Debug()
            .WriteTo.Console()
            .WriteTo.File("logs/sionyx-.log", rollingInterval: RollingInterval.Day, retainedFileCountLimit: 14)
            .CreateLogger();

        Log.Information("SIONYX Kiosk WPF starting, version {Version}", GetVersion());

        // ── Global exception handlers ────────────────────────────
        DispatcherUnhandledException += (_, ex) =>
        {
            Log.Fatal(ex.Exception, "Unhandled UI exception");
            ex.Handled = true;
        };
        AppDomain.CurrentDomain.UnhandledException += (_, ex) =>
        {
            Log.Fatal(ex.ExceptionObject as Exception, "Unhandled domain exception");
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
                // RegistryConfig is static, no DI needed

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

                // User-scoped services (created after login via factory)
                services.AddSingleton(sp =>
                {
                    var fb = sp.GetRequiredService<FirebaseClient>();
                    var auth = sp.GetRequiredService<AuthService>();
                    var cfg = sp.GetRequiredService<FirebaseConfig>();
                    return new SessionService(fb, auth.CurrentUser?.Uid ?? "", cfg.OrgId);
                });
                services.AddSingleton(sp =>
                {
                    var fb = sp.GetRequiredService<FirebaseClient>();
                    var auth = sp.GetRequiredService<AuthService>();
                    return new ChatService(fb, auth.CurrentUser?.Uid ?? "");
                });

                // System Services
                services.AddSingleton(sp =>
                {
                    var fb = sp.GetRequiredService<FirebaseClient>();
                    var auth = sp.GetRequiredService<AuthService>();
                    return new PrintMonitorService(fb, auth.CurrentUser?.Uid ?? "");
                });
                services.AddSingleton(_ => new KeyboardRestrictionService());
                services.AddSingleton(_ => new GlobalHotkeyService());
                services.AddSingleton(_ => new ProcessRestrictionService());
                services.AddSingleton(_ => new ProcessCleanupService());
                services.AddSingleton(_ => new BrowserCleanupService());

                // ViewModels
                services.AddTransient<AuthViewModel>();
                services.AddTransient<MainViewModel>();
                services.AddTransient<HomeViewModel>(sp =>
                {
                    var session = sp.GetRequiredService<SessionService>();
                    var chat = sp.GetRequiredService<ChatService>();
                    var auth = sp.GetRequiredService<AuthService>();
                    return new HomeViewModel(session, chat, auth.CurrentUser!);
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
                services.AddTransient<HomePage>();
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

    private void ShowAuthWindow()
    {
        var authVm = _host!.Services.GetRequiredService<AuthViewModel>();

        authVm.LoginSucceeded += () =>
        {
            Current.Dispatcher.Invoke(() =>
            {
                MainWindow?.Close();
                ShowMainWindow();
            });
        };

        authVm.RegistrationSucceeded += () =>
        {
            Current.Dispatcher.Invoke(() =>
            {
                MainWindow?.Close();
                ShowMainWindow();
            });
        };

        var authWindow = new AuthWindow(authVm);
        authWindow.Show();
        MainWindow = authWindow;

        // Try auto-login
        _ = TryAutoLoginAsync(authVm);
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
        mainVm.LogoutRequested += () =>
        {
            Current.Dispatcher.Invoke(() =>
            {
                mainWindow.Close();
                ShowAuthWindow();
            });
        };

        // Start system services
        StartSystemServices();

        mainWindow.Show();
        MainWindow = mainWindow;
    }

    private void StartSystemServices()
    {
        try
        {
            var auth = _host!.Services.GetRequiredService<AuthService>();
            var userId = auth.CurrentUser?.Uid ?? "";

            // Force logout listener
            var forceLogout = _host.Services.GetRequiredService<ForceLogoutService>();
            forceLogout.StartListening(userId);
            forceLogout.ForceLogout += reason =>
            {
                Log.Warning("Force logout received: {Reason}", reason);
                Current.Dispatcher.Invoke(async () =>
                {
                    await StopSystemServicesAsync();
                    await auth.LogoutAsync();
                    MainWindow?.Close();
                    ShowAuthWindow();
                });
            };

            // Chat service — start SSE listener for messages
            var chat = _host.Services.GetRequiredService<ChatService>();
            chat.StartListening();

            // Print monitor — start/stop with session
            var session = _host.Services.GetRequiredService<SessionService>();
            var printMonitor = _host.Services.GetRequiredService<PrintMonitorService>();
            session.SessionStarted += () => printMonitor.StartMonitoring();
            session.SessionEnded += _ => printMonitor.StopMonitoring();

            // Operating hours monitoring
            var hours = _host.Services.GetRequiredService<OperatingHoursService>();
            hours.StartMonitoring();

            // Process restriction (always in kiosk mode)
            if (_isKiosk)
            {
                var procRestrict = _host.Services.GetRequiredService<ProcessRestrictionService>();
                procRestrict.Start();

                var keyboard = _host.Services.GetRequiredService<KeyboardRestrictionService>();
                keyboard.Start();
            }

            // Global hotkey (admin exit) — needs window handle from MainWindow
            if (MainWindow != null)
            {
                var hwnd = new System.Windows.Interop.WindowInteropHelper(MainWindow).Handle;
                if (hwnd != IntPtr.Zero)
                {
                    var hotkey = _host.Services.GetRequiredService<GlobalHotkeyService>();
                    hotkey.Start(hwnd);
                    hotkey.AdminExitRequested += () =>
                    {
                        Current.Dispatcher.Invoke(async () =>
                        {
                            await StopSystemServicesAsync();
                            await auth.LogoutAsync();
                            Shutdown();
                        });
                    };
                }
            }

            Log.Information("System services started successfully (kiosk={IsKiosk})", _isKiosk);
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error starting system services");
        }
    }

    private async Task StopSystemServicesAsync()
    {
        try
        {
            _host?.Services.GetService<ChatService>()?.StopListening();
            _host?.Services.GetService<ForceLogoutService>()?.StopListening();
            _host?.Services.GetService<OperatingHoursService>()?.StopMonitoring();
            _host?.Services.GetService<ProcessRestrictionService>()?.Stop();
            _host?.Services.GetService<KeyboardRestrictionService>()?.Stop();
            _host?.Services.GetService<GlobalHotkeyService>()?.Stop();
            _host?.Services.GetService<PrintMonitorService>()?.StopMonitoring();

            var session = _host?.Services.GetService<SessionService>();
            if (session?.IsActive == true)
                await session.EndSessionAsync("logout");
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error stopping system services");
        }
    }

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

    private static string GetVersion() => "1.0.0";
}
