using System.Printing;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows.Threading;
using SionyxKiosk.Infrastructure;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Print Monitor - Event-Driven Per-Job Interception (Multi-PC Safe).
///
/// Architecture (PaperCut-style):
/// - EVENT-DRIVEN detection via FindFirstPrinterChangeNotification
/// - Fallback polling (2s) as a safety net
/// - Per-job: PAUSE IMMEDIATELY, then read info while frozen
/// - If paused: validate budget → approve (resume) or deny (cancel)
/// - If escaped: charge RETROACTIVELY with debt
///
/// Cost formula: pages × copies × price_per_page (BW or color)
///
/// Multi-PC safety: NEVER pauses printers at hardware level.
/// </summary>
public class PrintMonitorService : BaseService, IDisposable
{
    protected override string ServiceName => "PrintMonitorService";

    // P/Invoke constants
    private const uint PRINTER_CHANGE_ADD_JOB = 0x00000100;
    private const uint WAIT_OBJECT_0 = 0x00000000;
    private const int INVALID_HANDLE_VALUE = -1;
    private const int NOTIFICATION_WAIT_MS = 500;
    private const int FALLBACK_POLL_MS = 2000;

    // Job control commands
    private const int JOB_CONTROL_PAUSE = 1;
    private const int JOB_CONTROL_RESUME = 2;
    private const int JOB_CONTROL_CANCEL = 3;

    // Job status flags
    private const int JOB_STATUS_SPOOLING = 0x00000008;

    // DEVMODE color constants
    private const short DMCOLOR_COLOR = 2;

    // P/Invoke declarations
    [DllImport("winspool.drv", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool OpenPrinterW(string? pPrinterName, out IntPtr phPrinter, IntPtr pDefault);

    [DllImport("winspool.drv", SetLastError = true)]
    private static extern bool ClosePrinter(IntPtr hPrinter);

    [DllImport("winspool.drv", SetLastError = true)]
    private static extern IntPtr FindFirstPrinterChangeNotification(
        IntPtr hPrinter, uint fdwFilter, uint fdwOptions, IntPtr pPrinterNotifyOptions);

    [DllImport("winspool.drv", SetLastError = true)]
    private static extern bool FindNextPrinterChangeNotification(
        IntPtr hChange, out uint pdwChange, IntPtr pPrinterNotifyOptions, IntPtr ppPrinterNotifyInfo);

    [DllImport("winspool.drv", SetLastError = true)]
    private static extern bool FindClosePrinterChangeNotification(IntPtr hChange);

    [DllImport("winspool.drv", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool SetJobW(IntPtr hPrinter, uint jobId, uint level, IntPtr pJob, uint command);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    // State
    private string _userId;
    private bool _isMonitoring;
    private readonly object _lock = new();
    private readonly Dictionary<string, HashSet<int>> _knownJobs = new();
    private readonly HashSet<string> _processedJobs = new();

    // Notification thread
    private Thread? _notificationThread;
    private volatile bool _stopRequested;

    // Fallback polling timer
    private DispatcherTimer? _pollTimer;

    // Pricing cache
    private double _bwPrice = 1.0;
    private double _colorPrice = 3.0;

    // Budget cache
    private double? _cachedBudget;
    private DateTime? _budgetCacheTime;
    private const int BudgetCacheTtl = 30; // seconds

    // Events (replace PyQt signals)
    public event Action<string, int, double, double>? JobAllowed;   // doc, pages, cost, remaining
    public event Action<string, int, double, double>? JobBlocked;   // doc, pages, cost, budget
    public event Action<double>? BudgetUpdated;                      // new_budget
    public event Action<string>? ErrorOccurred;                      // error_message

    public PrintMonitorService(FirebaseClient firebase, string userId)
        : base(firebase)
    {
        _userId = userId;
    }

    public bool IsMonitoring => _isMonitoring;

    /// <summary>Update userId for a new login session (singleton reuse).</summary>
    public void Reinitialize(string userId)
    {
        StopMonitoring();
        _userId = userId;
        _cachedBudget = null;
        _budgetCacheTime = null;
    }

    // ==================== PUBLIC API ====================

    public void StartMonitoring()
    {
        if (_isMonitoring) return;

        Logger.Information("Starting print monitor (event-driven, multi-PC safe)");

        LoadPricing();
        InitializeKnownJobs();
        _processedJobs.Clear();
        _stopRequested = false;
        _isMonitoring = true;

        // PRIMARY: Event-driven notification thread
        _notificationThread = new Thread(NotificationThreadFunc)
        {
            IsBackground = true,
            Name = "PrintNotificationWatcher",
        };
        _notificationThread.Start();

        // FALLBACK: Polling timer
        _pollTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(FALLBACK_POLL_MS) };
        _pollTimer.Tick += (_, _) => ScanForNewJobs();
        _pollTimer.Start();

        Logger.Information("Print monitor started");
    }

    public void StopMonitoring()
    {
        if (!_isMonitoring) return;

        Logger.Information("Stopping print monitor");
        _isMonitoring = false;
        _stopRequested = true;

        _pollTimer?.Stop();
        _pollTimer = null;

        _notificationThread?.Join(TimeSpan.FromSeconds(2));
        _notificationThread = null;

        lock (_lock)
        {
            _knownJobs.Clear();
            _processedJobs.Clear();
        }

        Logger.Information("Print monitor stopped");
    }

    public void Dispose()
    {
        StopMonitoring();
        GC.SuppressFinalize(this);
    }

    // ==================== PRICING ====================

    private void LoadPricing()
    {
        try
        {
            // Run on a thread-pool thread to avoid deadlocking the UI thread.
            // Firebase methods use async/await without ConfigureAwait(false),
            // so calling .GetAwaiter().GetResult() from the Dispatcher thread
            // would deadlock (the continuation needs the Dispatcher, which is blocked).
            var result = Task.Run(() => Firebase.DbGetAsync("metadata")).GetAwaiter().GetResult();
            if (result.Success && result.Data is JsonElement data && data.ValueKind == JsonValueKind.Object)
            {
                _bwPrice = data.TryGetProperty("blackAndWhitePrice", out var bw) && bw.TryGetDouble(out var bwVal) ? bwVal : 1.0;
                _colorPrice = data.TryGetProperty("colorPrice", out var c) && c.TryGetDouble(out var cVal) ? cVal : 3.0;
                Logger.Information("Loaded pricing: B&W={Bw}₪, Color={Color}₪", _bwPrice, _colorPrice);
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error loading pricing");
        }
    }

    private double CalculateCost(int pages, int copies, bool isColor)
    {
        var pricePerPage = isColor ? _colorPrice : _bwPrice;
        return pages * copies * pricePerPage;
    }

    // ==================== BUDGET ====================

    private double GetUserBudget(bool forceRefresh = false)
    {
        if (!forceRefresh && _cachedBudget.HasValue && _budgetCacheTime.HasValue)
        {
            var age = (DateTime.Now - _budgetCacheTime.Value).TotalSeconds;
            if (age < BudgetCacheTtl) return _cachedBudget.Value;
        }

        try
        {
            var result = Task.Run(() => Firebase.DbGetAsync($"users/{_userId}")).GetAwaiter().GetResult();
            if (result.Success && result.Data is JsonElement data && data.ValueKind == JsonValueKind.Object)
            {
                var budget = data.TryGetProperty("printBalance", out var pb) && pb.TryGetDouble(out var pbVal) ? pbVal : 0.0;
                _cachedBudget = budget;
                _budgetCacheTime = DateTime.Now;
                return budget;
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error getting user budget");
        }
        return 0.0;
    }

    private bool DeductBudget(double amount, bool allowNegative = false)
    {
        try
        {
            var currentBudget = GetUserBudget(forceRefresh: true);
            var newBudget = allowNegative ? currentBudget - amount : Math.Max(0.0, currentBudget - amount);

            var result = Task.Run(() => Firebase.DbUpdateAsync($"users/{_userId}", new
            {
                printBalance = newBudget,
                updatedAt = DateTime.Now.ToString("o"),
            })).GetAwaiter().GetResult();

            if (result.Success)
            {
                _cachedBudget = newBudget;
                _budgetCacheTime = DateTime.Now;
                Logger.Information("Budget deducted: {Amount}₪, new balance: {Balance}₪", amount, newBudget);
                BudgetUpdated?.Invoke(newBudget);
                return true;
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error deducting budget");
        }
        return false;
    }

    // ==================== SPOOLER INTERACTION ====================

    private static List<string> GetAllPrinters()
    {
        var printers = new List<string>();
        try
        {
            using var server = new LocalPrintServer();
            foreach (var queue in server.GetPrintQueues())
            {
                printers.Add(queue.FullName);
                queue.Dispose();
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error enumerating printers");
        }
        return printers;
    }

    private static List<PrintSystemJobInfo> GetPrinterJobs(string printerName)
    {
        var jobs = new List<PrintSystemJobInfo>();
        try
        {
            using var server = new LocalPrintServer();
            using var queue = server.GetPrintQueue(printerName);
            queue.Refresh();
            foreach (var job in queue.GetPrintJobInfoCollection())
                jobs.Add(job);
        }
        catch (Exception ex)
        {
            Log.Debug("Error getting jobs for {Printer}: {Error}", printerName, ex.Message);
        }
        return jobs;
    }

    private static bool PauseJob(string printerName, int jobId)
    {
        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero)) return false;
        try
        {
            return SetJobW(hPrinter, (uint)jobId, 0, IntPtr.Zero, JOB_CONTROL_PAUSE);
        }
        catch
        {
            return false;
        }
        finally
        {
            ClosePrinter(hPrinter);
        }
    }

    private static bool ResumeJob(string printerName, int jobId)
    {
        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero)) return false;
        try
        {
            return SetJobW(hPrinter, (uint)jobId, 0, IntPtr.Zero, JOB_CONTROL_RESUME);
        }
        finally
        {
            ClosePrinter(hPrinter);
        }
    }

    private static bool CancelJob(string printerName, int jobId)
    {
        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero)) return false;
        try
        {
            return SetJobW(hPrinter, (uint)jobId, 0, IntPtr.Zero, JOB_CONTROL_CANCEL);
        }
        finally
        {
            ClosePrinter(hPrinter);
        }
    }

    // ==================== EVENT-DRIVEN NOTIFICATIONS ====================

    private void NotificationThreadFunc()
    {
        IntPtr hPrinter = IntPtr.Zero;
        IntPtr hChange = IntPtr.Zero;

        try
        {
            if (!OpenPrinterW(null, out hPrinter, IntPtr.Zero))
            {
                Logger.Warning("Could not open print server, using polling only");
                return;
            }

            hChange = FindFirstPrinterChangeNotification(hPrinter, PRINTER_CHANGE_ADD_JOB, 0, IntPtr.Zero);
            if (hChange == (IntPtr)INVALID_HANDLE_VALUE || hChange == IntPtr.Zero)
            {
                Logger.Warning("Could not create notification handle, using polling only");
                ClosePrinter(hPrinter);
                return;
            }

            Logger.Information("Notification handle created, watching for print jobs");

            while (!_stopRequested)
            {
                var result = WaitForSingleObject(hChange, NOTIFICATION_WAIT_MS);
                if (result == WAIT_OBJECT_0 && !_stopRequested)
                {
                    // Acknowledge notification
                    FindNextPrinterChangeNotification(hChange, out _, IntPtr.Zero, IntPtr.Zero);
                    Logger.Debug("Notification: new job event received");
                    ScanForNewJobs();
                }
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Notification thread error");
        }
        finally
        {
            if (hChange != IntPtr.Zero && hChange != (IntPtr)INVALID_HANDLE_VALUE)
                FindClosePrinterChangeNotification(hChange);
            if (hPrinter != IntPtr.Zero)
                ClosePrinter(hPrinter);

            Logger.Information("Notification thread exited");
        }
    }

    // ==================== JOB DETECTION ====================

    private void InitializeKnownJobs()
    {
        lock (_lock) _knownJobs.Clear();

        var printers = GetAllPrinters();
        if (printers.Count == 0)
        {
            Logger.Warning("No printers found! Print monitoring may not work.");
            return;
        }

        Logger.Information("Found {Count} printer(s)", printers.Count);

        foreach (var printer in printers)
        {
            var jobs = GetPrinterJobs(printer);
            lock (_lock)
            {
                _knownJobs[printer] = new HashSet<int>(jobs.Select(j => j.JobIdentifier));
            }
        }
    }

    private void ScanForNewJobs()
    {
        if (!_isMonitoring) return;

        try
        {
            var printers = GetAllPrinters();
            foreach (var printer in printers)
            {
                HashSet<int> known;
                lock (_lock)
                {
                    if (!_knownJobs.ContainsKey(printer))
                        _knownJobs[printer] = new HashSet<int>();
                    known = new HashSet<int>(_knownJobs[printer]);
                }

                var currentJobs = GetPrinterJobs(printer);
                var currentIds = new HashSet<int>(currentJobs.Select(j => j.JobIdentifier));
                var newIds = currentIds.Except(known);

                foreach (var jobId in newIds)
                {
                    var jobKey = $"{printer}:{jobId}";
                    lock (_lock)
                    {
                        if (_processedJobs.Contains(jobKey)) continue;
                        _processedJobs.Add(jobKey);
                    }

                    var job = currentJobs.FirstOrDefault(j => j.JobIdentifier == jobId);
                    if (job != null)
                    {
                        Logger.Information("New print job: ID={JobId} on '{Printer}'", jobId, printer);
                        HandleNewJob(printer, job);
                    }
                }

                lock (_lock)
                {
                    _knownJobs[printer] = currentIds;

                    // Clean up processed set
                    var prefix = $"{printer}:";
                    _processedJobs.RemoveWhere(key =>
                        key.StartsWith(prefix) &&
                        int.TryParse(key[(prefix.Length)..], out var id) &&
                        !currentIds.Contains(id));
                }
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error scanning print queues");
        }
    }

    // ==================== JOB HANDLING ====================

    private void HandleNewJob(string printerName, PrintSystemJobInfo job)
    {
        var jobId = job.JobIdentifier;
        var docName = job.Name ?? "Unknown";

        // STEP 1: PAUSE IMMEDIATELY
        var paused = PauseJob(printerName, jobId);

        // Extract details
        var pages = Math.Max(1, job.NumberOfPages);
        var copies = Math.Max(1, job.NumberOfPagesPrinted > 0 ? 1 : 1); // Copies from DEVMODE not available in System.Printing easily
        var isColor = false; // Default to B&W (user-friendly)

        // Try to get color info from the print ticket
        try
        {
            using var server = new LocalPrintServer();
            using var queue = server.GetPrintQueue(printerName);
            var ticket = queue.UserPrintTicket;
            if (ticket?.OutputColor != null)
            {
                isColor = ticket.OutputColor == OutputColor.Color;
            }
        }
        catch { /* Use defaults */ }

        var billablePages = pages * copies;
        var cost = CalculateCost(pages, copies, isColor);

        Logger.Information("Job {JobId}: '{Doc}' - {Pages}p × {Copies}c, {ColorType}, cost={Cost}₪",
            jobId, docName, pages, copies, isColor ? "COLOR" : "B&W", cost);

        if (paused)
        {
            HandlePausedJob(printerName, jobId, docName, billablePages, cost);
        }
        else
        {
            HandleEscapedJob(docName, billablePages, cost);
        }
    }

    private void HandlePausedJob(string printerName, int jobId, string docName, int billablePages, double cost)
    {
        var budget = GetUserBudget(forceRefresh: true);

        if (budget >= cost)
        {
            if (DeductBudget(cost))
            {
                ResumeJob(printerName, jobId);
                var remaining = budget - cost;
                Logger.Information("Job APPROVED: '{Doc}' - {Cost}₪, remaining {Remaining}₪", docName, cost, remaining);
                JobAllowed?.Invoke(docName, billablePages, cost, remaining);
            }
            else
            {
                CancelJob(printerName, jobId);
                Logger.Error("Budget deduction failed for job {JobId}, cancelling", jobId);
                ErrorOccurred?.Invoke("שגיאה בחיוב הדפסה");
            }
        }
        else
        {
            CancelJob(printerName, jobId);
            Logger.Warning("Job DENIED: '{Doc}' - need {Cost}₪, have {Budget}₪", docName, cost, budget);
            JobBlocked?.Invoke(docName, billablePages, cost, budget);
        }
    }

    private void HandleEscapedJob(string docName, int billablePages, double cost)
    {
        Logger.Warning("Job escaped pause: '{Doc}' - charging retroactively", docName);

        var budget = GetUserBudget(forceRefresh: true);

        if (DeductBudget(cost, allowNegative: true))
        {
            var remaining = budget - cost;
            if (remaining < 0)
                Logger.Warning("Retroactive charge created DEBT: '{Doc}' - {Cost}₪, balance now {Balance}₪", docName, cost, remaining);
            else
                Logger.Information("Retroactive charge: '{Doc}' - {Cost}₪, remaining {Remaining}₪", docName, cost, remaining);

            JobAllowed?.Invoke(docName, billablePages, cost, remaining);
        }
        else
        {
            Logger.Error("Retroactive deduction failed for '{Doc}'", docName);
            ErrorOccurred?.Invoke("שגיאה בחיוב הדפסה");
        }
    }
}
