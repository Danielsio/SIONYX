using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using SionyxKiosk.Infrastructure;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Print Monitor — Event-Driven Per-Job Interception (Multi-PC Safe).
///
/// Architecture:
///   10 PCs share network printers. Each PC runs this monitor on its LOCAL
///   spooler. Jobs are paused/resumed/cancelled at the JOB level — the
///   physical printer is never touched, so cross-PC jobs are unaffected.
///
/// Detection:
///   PRIMARY — FindFirstPrinterChangeNotification (instant, event-driven)
///   FALLBACK — Background polling every 2 seconds (safety net)
///   Both run on background threads; the UI thread is never blocked.
///
/// Per-job flow:
///   1. New job detected → PAUSE immediately in local spooler
///   2. Wait for spooling to finish (retry loop, up to 3s)
///   3. Read accurate page count, copies, and color from DEVMODE
///   4. Calculate cost → check budget → RESUME (approve) or CANCEL (deny)
///   5. If pause failed (escaped): charge retroactively, allow debt
///
/// Thread safety:
///   All spooler access uses P/Invoke (no System.Printing COM objects).
///   A SemaphoreSlim(1,1) prevents concurrent scans from the notification
///   thread and the fallback poll thread.
///
/// Cost formula: pages × copies × price_per_page (BW or color)
/// </summary>
public class PrintMonitorService : BaseService, IDisposable
{
    protected override string ServiceName => "PrintMonitorService";

    // ==================== P/Invoke Constants ====================

    private const uint PRINTER_CHANGE_ADD_JOB = 0x00000100;
    private const uint WAIT_OBJECT_0 = 0x00000000;
    private const int INVALID_HANDLE = -1;
    private const int NOTIFICATION_WAIT_MS = 500;
    private const int FALLBACK_POLL_MS = 2000;

    private const int JOB_CONTROL_PAUSE = 1;
    private const int JOB_CONTROL_RESUME = 2;
    private const int JOB_CONTROL_CANCEL = 3;

    private const short DMCOLOR_MONOCHROME = 1;
    private const short DMCOLOR_COLOR = 2;
    private const uint DM_COLOR = 0x00000800; // dmFields flag for dmColor validity

    private const uint PRINTER_ENUM_LOCAL = 0x00000002;
    private const uint PRINTER_ENUM_CONNECTIONS = 0x00000004;

    private const int SPOOL_WAIT_MAX_MS = 3000;
    private const int SPOOL_WAIT_INTERVAL_MS = 250;

    // ==================== P/Invoke Structs ====================

    [StructLayout(LayoutKind.Sequential)]
    private struct SYSTEMTIME
    {
        public ushort wYear, wMonth, wDayOfWeek, wDay;
        public ushort wHour, wMinute, wSecond, wMilliseconds;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct JOB_INFO_1W
    {
        public uint JobId;
        public IntPtr pPrinterName;
        public IntPtr pMachineName;
        public IntPtr pUserName;
        public IntPtr pDocument;
        public IntPtr pDatatype;
        public IntPtr pStatus;
        public uint Status;
        public uint Priority;
        public uint Position;
        public uint TotalPages;
        public uint PagesPrinted;
        public SYSTEMTIME Submitted;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct JOB_INFO_2W
    {
        public uint JobId;
        public IntPtr pPrinterName;
        public IntPtr pMachineName;
        public IntPtr pUserName;
        public IntPtr pDocument;
        public IntPtr pNotifyName;
        public IntPtr pDatatype;
        public IntPtr pPrintProcessor;
        public IntPtr pParameters;
        public IntPtr pDriverName;
        public IntPtr pDevMode;
        public IntPtr pStatus;
        public IntPtr pSecurityDescriptor;
        public uint Status;
        public uint Priority;
        public uint Position;
        public uint StartTime;
        public uint UntilTime;
        public uint TotalPages;
        public uint Size;
        public SYSTEMTIME Submitted;
        public uint Time;
        public uint PagesPrinted;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct DEVMODEW
    {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string dmDeviceName;
        public ushort dmSpecVersion;
        public ushort dmDriverVersion;
        public ushort dmSize;
        public ushort dmDriverExtra;
        public uint dmFields;
        public short dmOrientation;
        public short dmPaperSize;
        public short dmPaperLength;
        public short dmPaperWidth;
        public short dmScale;
        public short dmCopies;
        public short dmDefaultSource;
        public short dmPrintQuality;
        public short dmColor;
        public short dmDuplex;
        public short dmYResolution;
        public short dmTTOption;
        public short dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string dmFormName;
        public ushort dmLogPixels;
        public uint dmBitsPerPel;
        public uint dmPelsWidth;
        public uint dmPelsHeight;
        public uint dmDisplayFlags;
        public uint dmDisplayFrequency;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct PRINTER_INFO_1W
    {
        public uint Flags;
        public IntPtr pDescription;
        public IntPtr pName;
        public IntPtr pComment;
    }

    // ==================== P/Invoke Declarations ====================

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

    [DllImport("winspool.drv", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool GetJobW(
        IntPtr hPrinter, uint jobId, uint level,
        IntPtr pJob, uint cbBuf, out uint pcbNeeded);

    [DllImport("winspool.drv", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool EnumJobsW(
        IntPtr hPrinter, uint firstJob, uint noJobs, uint level,
        IntPtr pJob, uint cbBuf, out uint pcbNeeded, out uint pcReturned);

    [DllImport("winspool.drv", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool EnumPrintersW(
        uint flags, string? name, uint level,
        IntPtr pPrinterEnum, uint cbBuf, out uint pcbNeeded, out uint pcReturned);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    // ==================== State ====================

    private string _userId;
    private bool _isMonitoring;
    private readonly SemaphoreSlim _scanLock = new(1, 1);
    private readonly Dictionary<string, HashSet<int>> _knownJobs = new();
    private readonly HashSet<string> _processedJobs = new();

    // Threads
    private Thread? _notificationThread;
    private Thread? _pollThread;
    private volatile bool _stopRequested;

    // Pricing
    private double _bwPrice = 1.0;
    private double _colorPrice = 3.0;

    // Budget cache
    private double? _cachedBudget;
    private DateTime? _budgetCacheTime;
    private const int BudgetCacheTtlSec = 30;

    // Events
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

        Logger.Information("Starting print monitor (event-driven + fallback poll, multi-PC safe)");

        LoadPricing();
        InitializeKnownJobs();
        _processedJobs.Clear();
        _stopRequested = false;
        _isMonitoring = true;

        // PRIMARY: Event-driven notification (background thread)
        _notificationThread = new Thread(NotificationThreadFunc)
        {
            IsBackground = true,
            Name = "PrintNotificationWatcher",
        };
        _notificationThread.Start();

        // FALLBACK: Polling (background thread — NOT DispatcherTimer)
        _pollThread = new Thread(PollThreadFunc)
        {
            IsBackground = true,
            Name = "PrintFallbackPoller",
        };
        _pollThread.Start();

        Logger.Information("Print monitor started");
    }

    public void StopMonitoring()
    {
        if (!_isMonitoring) return;

        Logger.Information("Stopping print monitor");
        _isMonitoring = false;
        _stopRequested = true;

        _notificationThread?.Join(TimeSpan.FromSeconds(3));
        _notificationThread = null;

        _pollThread?.Join(TimeSpan.FromSeconds(3));
        _pollThread = null;

        lock (_knownJobs)
        {
            _knownJobs.Clear();
        }
        lock (_processedJobs)
        {
            _processedJobs.Clear();
        }

        Logger.Information("Print monitor stopped");
    }

    public void Dispose()
    {
        StopMonitoring();
        _scanLock.Dispose();
        GC.SuppressFinalize(this);
    }

    // ==================== PRINTER ENUMERATION (P/Invoke) ====================

    private static List<string> GetAllPrinters()
    {
        var printers = new List<string>();
        try
        {
            uint flags = PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS;

            // First call: get required buffer size
            EnumPrintersW(flags, null, 1, IntPtr.Zero, 0, out uint needed, out _);
            if (needed == 0) return printers;

            var buf = Marshal.AllocHGlobal((int)needed);
            try
            {
                if (!EnumPrintersW(flags, null, 1, buf, needed, out _, out uint count))
                    return printers;

                int structSize = Marshal.SizeOf<PRINTER_INFO_1W>();
                for (int i = 0; i < count; i++)
                {
                    var info = Marshal.PtrToStructure<PRINTER_INFO_1W>(buf + i * structSize);
                    if (info.pName != IntPtr.Zero)
                    {
                        var name = Marshal.PtrToStringUni(info.pName);
                        if (!string.IsNullOrEmpty(name))
                            printers.Add(name);
                    }
                }
            }
            finally
            {
                Marshal.FreeHGlobal(buf);
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error enumerating printers");
        }
        return printers;
    }

    // ==================== JOB ENUMERATION (P/Invoke) ====================

    private static List<int> GetJobIds(string printerName)
    {
        var jobIds = new List<int>();
        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero))
            return jobIds;

        try
        {
            // First call: get required buffer size
            EnumJobsW(hPrinter, 0, 999, 1, IntPtr.Zero, 0, out uint needed, out _);
            if (needed == 0) return jobIds;

            var buf = Marshal.AllocHGlobal((int)needed);
            try
            {
                if (!EnumJobsW(hPrinter, 0, 999, 1, buf, needed, out _, out uint count))
                    return jobIds;

                int structSize = Marshal.SizeOf<JOB_INFO_1W>();
                for (int i = 0; i < count; i++)
                {
                    var info = Marshal.PtrToStructure<JOB_INFO_1W>(buf + i * structSize);
                    jobIds.Add((int)info.JobId);
                }
            }
            finally
            {
                Marshal.FreeHGlobal(buf);
            }
        }
        catch (Exception ex)
        {
            Log.Debug("Error getting jobs for {Printer}: {Error}", printerName, ex.Message);
        }
        finally
        {
            ClosePrinter(hPrinter);
        }
        return jobIds;
    }

    // ==================== JOB DETAILS (P/Invoke + DEVMODE) ====================

    private record struct JobDetails(string DocName, int Pages, int Copies, bool IsColor);

    /// <summary>
    /// Read full job details via GetJob level 2, including DEVMODE for copies and color.
    /// </summary>
    private static JobDetails ReadJobDetails(string printerName, int jobId)
    {
        var fallback = new JobDetails("Unknown", 0, 1, false);

        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero))
            return fallback;

        try
        {
            // First call: get required buffer size
            GetJobW(hPrinter, (uint)jobId, 2, IntPtr.Zero, 0, out uint needed);
            if (needed == 0) return fallback;

            var buf = Marshal.AllocHGlobal((int)needed);
            try
            {
                if (!GetJobW(hPrinter, (uint)jobId, 2, buf, needed, out _))
                    return fallback;

                var info = Marshal.PtrToStructure<JOB_INFO_2W>(buf);

                var docName = info.pDocument != IntPtr.Zero
                    ? Marshal.PtrToStringUni(info.pDocument) ?? "Unknown"
                    : "Unknown";

                var pages = (int)info.TotalPages;
                var copies = 1;
                var isColor = false;

                // Read DEVMODE for copies and color
                if (info.pDevMode != IntPtr.Zero)
                {
                    try
                    {
                        var devMode = Marshal.PtrToStructure<DEVMODEW>(info.pDevMode);
                        if (devMode.dmCopies > 0)
                            copies = devMode.dmCopies;

                        // Color detection: only trust dmColor when dmFields
                        // explicitly includes DM_COLOR. Many drivers leave
                        // dmColor=2 (COLOR) as a default even for grayscale
                        // jobs, so we default to B&W when uncertain.
                        if ((devMode.dmFields & DM_COLOR) != 0)
                        {
                            isColor = devMode.dmColor == DMCOLOR_COLOR;
                            Log.Debug(
                                "DEVMODE dmColor={Color} (DM_COLOR flag SET), isColor={IsColor}",
                                devMode.dmColor, isColor);
                        }
                        else
                        {
                            // DM_COLOR flag not set — driver didn't populate
                            // the field. Default to B&W (cheaper, safer).
                            isColor = false;
                            Log.Debug(
                                "DEVMODE dmColor={Color} but DM_COLOR flag NOT SET in dmFields=0x{Fields:X} — defaulting to B&W",
                                devMode.dmColor, devMode.dmFields);
                        }
                    }
                    catch (Exception ex)
                    {
                        Log.Debug("DEVMODE read failed: {Error} — defaulting to B&W", ex.Message);
                    }
                }
                else
                {
                    Log.Debug("pDevMode is NULL for job {JobId} — defaulting to B&W", jobId);
                }

                return new JobDetails(docName, pages, copies, isColor);
            }
            finally
            {
                Marshal.FreeHGlobal(buf);
            }
        }
        catch (Exception ex)
        {
            Log.Debug("Error reading job details for {JobId}: {Error}", jobId, ex.Message);
            return fallback;
        }
        finally
        {
            ClosePrinter(hPrinter);
        }
    }

    /// <summary>
    /// Wait for spooling to complete, then return accurate job details.
    /// Retries reading until TotalPages stabilizes or timeout.
    /// </summary>
    private static JobDetails WaitForJobDetails(string printerName, int jobId)
    {
        var sw = Stopwatch.StartNew();
        int lastPages = 0;
        int stableCount = 0;
        JobDetails latest = new("Unknown", 0, 1, false);

        while (sw.ElapsedMilliseconds < SPOOL_WAIT_MAX_MS)
        {
            latest = ReadJobDetails(printerName, jobId);

            if (latest.Pages > 0)
            {
                if (latest.Pages == lastPages)
                {
                    stableCount++;
                    if (stableCount >= 2) // Stable for 2 consecutive reads
                        return latest;
                }
                else
                {
                    stableCount = 0;
                }
                lastPages = latest.Pages;
            }

            Thread.Sleep(SPOOL_WAIT_INTERVAL_MS);
        }

        // Timeout — return best known, at least 1 page
        return latest with { Pages = Math.Max(1, latest.Pages) };
    }

    // ==================== JOB CONTROL (P/Invoke) ====================

    private static bool PauseJob(string printerName, int jobId)
    {
        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero)) return false;
        try { return SetJobW(hPrinter, (uint)jobId, 0, IntPtr.Zero, JOB_CONTROL_PAUSE); }
        catch { return false; }
        finally { ClosePrinter(hPrinter); }
    }

    private static bool ResumeJob(string printerName, int jobId)
    {
        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero)) return false;
        try { return SetJobW(hPrinter, (uint)jobId, 0, IntPtr.Zero, JOB_CONTROL_RESUME); }
        finally { ClosePrinter(hPrinter); }
    }

    private static bool CancelJob(string printerName, int jobId)
    {
        if (!OpenPrinterW(printerName, out var hPrinter, IntPtr.Zero)) return false;
        try { return SetJobW(hPrinter, (uint)jobId, 0, IntPtr.Zero, JOB_CONTROL_CANCEL); }
        finally { ClosePrinter(hPrinter); }
    }

    // ==================== PRICING ====================

    private void LoadPricing()
    {
        try
        {
            var result = Task.Run(() => Firebase.DbGetAsync("metadata")).GetAwaiter().GetResult();
            if (result.Success && result.Data is JsonElement data && data.ValueKind == JsonValueKind.Object)
            {
                _bwPrice = data.TryGetProperty("blackAndWhitePrice", out var bw) && bw.TryGetDouble(out var bwVal) ? bwVal : 1.0;
                _colorPrice = data.TryGetProperty("colorPrice", out var c) && c.TryGetDouble(out var cVal) ? cVal : 3.0;
                Logger.Information("Pricing loaded from DB: B&W={Bw}₪/page, Color={Color}₪/page", _bwPrice, _colorPrice);
            }
            else
            {
                Logger.Warning("Failed to load pricing from DB (success={Success}) — using defaults: B&W={Bw}₪, Color={Color}₪",
                    result.Success, _bwPrice, _colorPrice);
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error loading pricing, using defaults: B&W={Bw}₪, Color={Color}₪", _bwPrice, _colorPrice);
        }
    }

    /// <summary>Calculate print cost: pages × copies × price_per_page.</summary>
    private double CalculateCost(int pages, int copies, bool isColor)
    {
        return pages * copies * (isColor ? _colorPrice : _bwPrice);
    }

    // ==================== BUDGET ====================

    private double GetUserBudget(bool forceRefresh = false)
    {
        if (!forceRefresh && _cachedBudget.HasValue && _budgetCacheTime.HasValue)
        {
            if ((DateTime.UtcNow - _budgetCacheTime.Value).TotalSeconds < BudgetCacheTtlSec)
                return _cachedBudget.Value;
        }

        try
        {
            var result = Task.Run(() => Firebase.DbGetAsync($"users/{_userId}")).GetAwaiter().GetResult();
            if (result.Success && result.Data is JsonElement data && data.ValueKind == JsonValueKind.Object)
            {
                var budget = data.TryGetProperty("printBalance", out var pb) && pb.TryGetDouble(out var val) ? val : 0.0;
                _cachedBudget = budget;
                _budgetCacheTime = DateTime.UtcNow;
                return budget;
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error getting user budget");
        }
        return _cachedBudget ?? 0.0;
    }

    private bool DeductBudget(double amount, bool allowNegative = false)
    {
        try
        {
            var currentBudget = GetUserBudget(forceRefresh: true);
            var newBudget = allowNegative
                ? currentBudget - amount
                : Math.Max(0.0, currentBudget - amount);

            var result = Task.Run(() => Firebase.DbUpdateAsync($"users/{_userId}", new
            {
                printBalance = newBudget,
                updatedAt = DateTime.Now.ToString("o"),
            })).GetAwaiter().GetResult();

            if (result.Success)
            {
                _cachedBudget = newBudget;
                _budgetCacheTime = DateTime.UtcNow;
                Logger.Information("Budget deducted: {Amount}₪ → balance: {Balance}₪", amount, newBudget);
                DispatchEvent(() => BudgetUpdated?.Invoke(newBudget));
                return true;
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error deducting budget");
        }
        return false;
    }

    // ==================== EVENT DISPATCH ====================

    /// <summary>Dispatch an action to the UI thread (safe from background threads).</summary>
    private static void DispatchEvent(Action action)
    {
        var dispatcher = System.Windows.Application.Current?.Dispatcher;
        if (dispatcher != null && !dispatcher.CheckAccess())
            dispatcher.BeginInvoke(action);
        else
            action();
    }

    // ==================== NOTIFICATION THREAD ====================

    private void NotificationThreadFunc()
    {
        IntPtr hPrinter = IntPtr.Zero;
        IntPtr hChange = IntPtr.Zero;

        try
        {
            if (!OpenPrinterW(null, out hPrinter, IntPtr.Zero))
            {
                Logger.Warning("Could not open print server handle — relying on fallback polling");
                return;
            }

            hChange = FindFirstPrinterChangeNotification(hPrinter, PRINTER_CHANGE_ADD_JOB, 0, IntPtr.Zero);
            if (hChange == (IntPtr)INVALID_HANDLE || hChange == IntPtr.Zero)
            {
                Logger.Warning("Could not create change notification — relying on fallback polling");
                ClosePrinter(hPrinter);
                return;
            }

            Logger.Information("Notification handle created — watching for new print jobs");

            while (!_stopRequested)
            {
                var result = WaitForSingleObject(hChange, NOTIFICATION_WAIT_MS);
                if (result == WAIT_OBJECT_0 && !_stopRequested)
                {
                    FindNextPrinterChangeNotification(hChange, out _, IntPtr.Zero, IntPtr.Zero);
                    Logger.Debug("Notification: new job event");
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
            if (hChange != IntPtr.Zero && hChange != (IntPtr)INVALID_HANDLE)
                FindClosePrinterChangeNotification(hChange);
            if (hPrinter != IntPtr.Zero)
                ClosePrinter(hPrinter);

            Logger.Information("Notification thread exited");
        }
    }

    // ==================== FALLBACK POLL THREAD ====================

    private void PollThreadFunc()
    {
        Logger.Information("Fallback poll thread started ({Interval}ms)", FALLBACK_POLL_MS);
        while (!_stopRequested)
        {
            Thread.Sleep(FALLBACK_POLL_MS);
            if (!_stopRequested)
                ScanForNewJobs();
        }
        Logger.Information("Fallback poll thread exited");
    }

    // ==================== JOB SCANNING ====================

    private void InitializeKnownJobs()
    {
        lock (_knownJobs) _knownJobs.Clear();

        var printers = GetAllPrinters();
        if (printers.Count == 0)
        {
            Logger.Warning("No printers found — print monitoring may not work");
            return;
        }

        Logger.Information("Found {Count} printer(s)", printers.Count);

        foreach (var printer in printers)
        {
            var jobIds = GetJobIds(printer);
            lock (_knownJobs)
            {
                _knownJobs[printer] = new HashSet<int>(jobIds);
            }
        }
    }

    /// <summary>
    /// Scan all printers for new jobs. Protected by SemaphoreSlim — if a scan
    /// is already in progress (from the other thread), this call is skipped.
    /// </summary>
    private void ScanForNewJobs()
    {
        if (!_isMonitoring) return;

        // Non-blocking: if another scan is running, skip this one
        if (!_scanLock.Wait(0)) return;

        try
        {
            var printers = GetAllPrinters();
            foreach (var printer in printers)
            {
                HashSet<int> known;
                lock (_knownJobs)
                {
                    if (!_knownJobs.ContainsKey(printer))
                        _knownJobs[printer] = new HashSet<int>();
                    known = new HashSet<int>(_knownJobs[printer]);
                }

                var currentIds = GetJobIds(printer);
                var currentSet = new HashSet<int>(currentIds);

                foreach (var jobId in currentIds)
                {
                    if (known.Contains(jobId)) continue;

                    var jobKey = $"{printer}:{jobId}";
                    bool shouldProcess;
                    lock (_processedJobs)
                    {
                        shouldProcess = _processedJobs.Add(jobKey);
                    }

                    if (shouldProcess)
                    {
                        Logger.Information("New print job detected: ID={JobId} on '{Printer}'", jobId, printer);
                        HandleNewJob(printer, jobId);
                    }
                }

                lock (_knownJobs)
                {
                    _knownJobs[printer] = currentSet;
                }

                // Prune processed keys for completed jobs
                lock (_processedJobs)
                {
                    var prefix = $"{printer}:";
                    _processedJobs.RemoveWhere(key =>
                        key.StartsWith(prefix) &&
                        int.TryParse(key[prefix.Length..], out var id) &&
                        !currentSet.Contains(id));
                }
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error scanning print queues");
        }
        finally
        {
            _scanLock.Release();
        }
    }

    // ==================== JOB HANDLING ====================

    private void HandleNewJob(string printerName, int jobId)
    {
        // STEP 1: PAUSE IMMEDIATELY (before spooling finishes)
        var paused = PauseJob(printerName, jobId);

        // STEP 2: Wait for spooling, then read accurate details from DEVMODE
        var details = WaitForJobDetails(printerName, jobId);

        var billablePages = details.Pages * details.Copies;
        var cost = CalculateCost(details.Pages, details.Copies, details.IsColor);

        Logger.Information(
            "Job {JobId}: '{Doc}' — {Pages}p × {Copies}c, {Color}, price/page={PricePerPage}₪, total={Cost}₪",
            jobId, details.DocName, details.Pages, details.Copies,
            details.IsColor ? "COLOR" : "B&W",
            details.IsColor ? _colorPrice : _bwPrice, cost);

        if (paused)
            HandlePausedJob(printerName, jobId, details.DocName, billablePages, cost);
        else
            HandleEscapedJob(details.DocName, billablePages, cost);
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
                Logger.Information("Job APPROVED: '{Doc}' — {Cost}₪, remaining {Remaining}₪", docName, cost, remaining);
                DispatchEvent(() => JobAllowed?.Invoke(docName, billablePages, cost, remaining));
            }
            else
            {
                CancelJob(printerName, jobId);
                Logger.Error("Budget deduction failed for job {JobId} — cancelling", jobId);
                DispatchEvent(() => ErrorOccurred?.Invoke("שגיאה בחיוב הדפסה"));
            }
        }
        else
        {
            CancelJob(printerName, jobId);
            Logger.Warning("Job DENIED: '{Doc}' — need {Cost}₪, have {Budget}₪", docName, cost, budget);
            DispatchEvent(() => JobBlocked?.Invoke(docName, billablePages, cost, budget));
        }
    }

    private void HandleEscapedJob(string docName, int billablePages, double cost)
    {
        Logger.Warning("Job escaped pause: '{Doc}' — charging retroactively", docName);

        var budget = GetUserBudget(forceRefresh: true);

        if (DeductBudget(cost, allowNegative: true))
        {
            var remaining = budget - cost;
            if (remaining < 0)
                Logger.Warning("Retroactive charge created DEBT: balance={Balance}₪", remaining);

            DispatchEvent(() => JobAllowed?.Invoke(docName, billablePages, cost, remaining));
        }
        else
        {
            Logger.Error("Retroactive deduction failed for '{Doc}'", docName);
            DispatchEvent(() => ErrorOccurred?.Invoke("שגיאה בחיוב הדפסה"));
        }
    }
}
