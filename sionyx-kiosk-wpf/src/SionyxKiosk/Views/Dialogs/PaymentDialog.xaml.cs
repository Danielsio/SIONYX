using System.IO;
using System.Text.Json;
using System.Windows;
using Microsoft.Web.WebView2.Core;
using Serilog;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.Views.Dialogs;

/// <summary>
/// Payment dialog with WebView2 bridge.
/// Loads payment.html via LocalFileServer, communicates with JS via PostWebMessage.
/// </summary>
public partial class PaymentDialog : Window
{
    private static readonly ILogger Logger = Log.ForContext<PaymentDialog>();

    private readonly PurchaseService _purchaseService;
    private readonly OrganizationMetadataService _metadataService;
    private readonly string _userId;
    private readonly Package _package;
    private readonly FirebaseClient _firebase;

    private LocalFileServer? _server;
    private string? _purchaseId;
    private SseListener? _statusListener;

    public bool PaymentSucceeded { get; private set; }

    public PaymentDialog(
        PurchaseService purchaseService,
        OrganizationMetadataService metadataService,
        FirebaseClient firebase,
        string userId,
        Package package)
    {
        _purchaseService = purchaseService;
        _metadataService = metadataService;
        _firebase = firebase;
        _userId = userId;
        _package = package;

        InitializeComponent();
        Loaded += OnLoaded;
        Closed += OnClosed;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        try
        {
            // Start local file server to serve payment.html
            var templatesDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Assets", "templates");
            _server = new LocalFileServer(templatesDir, 0); // Port 0 = auto-pick free port
            _server.Start();

            // Initialize WebView2
            await PaymentWebView.EnsureCoreWebView2Async();
            PaymentWebView.CoreWebView2.WebMessageReceived += OnWebMessageReceived;

            // Navigate to payment page
            var url = _server.BaseUrl + "payment.html";
            Logger.Information("Loading payment page: {Url}", url);
            PaymentWebView.CoreWebView2.Navigate(url);

            // Wait for page load, then inject config
            PaymentWebView.CoreWebView2.NavigationCompleted += async (_, args) =>
            {
                if (!args.IsSuccess) return;
                await InjectConfigAsync();
            };
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Failed to load payment dialog");
            MessageBox.Show("שגיאה בטעינת דף התשלום", "שגיאה", MessageBoxButton.OK, MessageBoxImage.Error);
            Close();
        }
    }

    private async Task InjectConfigAsync()
    {
        try
        {
            // Get Nedarim credentials from org metadata
            var metaResult = await _metadataService.GetOrganizationMetadataAsync(_firebase.OrgId);
            var mosadId = "";
            var apiValid = "";
            var callbackUrl = "";

            if (metaResult.IsSuccess && metaResult.Data is JsonElement meta)
            {
                if (meta.TryGetProperty("nedarimPlus", out var nedarim))
                {
                    mosadId = nedarim.TryGetProperty("mosadId", out var m) ? m.GetString() ?? "" : "";
                    apiValid = nedarim.TryGetProperty("apiValid", out var a) ? a.GetString() ?? "" : "";
                    callbackUrl = nedarim.TryGetProperty("callbackUrl", out var c) ? c.GetString() ?? "" : "";
                }
            }

            var config = new
            {
                mosadId,
                apiValid,
                amount = _package.Price.ToString("F0"),
                packageName = _package.Name ?? "",
                packageMinutes = _package.Minutes.ToString(),
                packagePrints = _package.Prints.ToString(),
                userName = "",
                orgId = _firebase.OrgId,
                callbackUrl
            };

            var configJson = JsonSerializer.Serialize(config);
            var message = JsonSerializer.Serialize(new { action = "setConfig", config });
            PaymentWebView.CoreWebView2.PostWebMessageAsJson(message);

            Logger.Information("Payment config injected for package: {Package}", _package.Name);
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Failed to inject payment config");
        }
    }

    private async void OnWebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs e)
    {
        try
        {
            var json = e.WebMessageAsJson;
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            var action = root.GetProperty("action").GetString();

            switch (action)
            {
                case "createPendingPurchase":
                    await HandleCreatePurchaseAsync();
                    break;

                case "paymentSuccess":
                    await HandlePaymentSuccessAsync(root);
                    break;

                case "close":
                    var success = root.TryGetProperty("success", out var s) && s.GetBoolean();
                    PaymentSucceeded = success;
                    Dispatcher.Invoke(Close);
                    break;
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error handling web message");
        }
    }

    private async Task HandleCreatePurchaseAsync()
    {
        try
        {
            var result = await _purchaseService.CreatePendingPurchaseAsync(_userId, _package);
            if (result.IsSuccess && result.Data is { } data)
            {
                // Extract purchaseId from anonymous object
                var type = data.GetType();
                _purchaseId = type.GetProperty("purchaseId")?.GetValue(data)?.ToString() ?? "";

                // Start listening for purchase status changes
                StartPurchaseStatusListener(_purchaseId);

                // Post purchase ID back to JS
                var msg = JsonSerializer.Serialize(new { action = "purchaseCreated", purchaseId = _purchaseId });
                Dispatcher.Invoke(() => PaymentWebView.CoreWebView2.PostWebMessageAsJson(msg));
                Logger.Information("Pending purchase created: {PurchaseId}", _purchaseId);
            }
            else
            {
                var errorMsg = JsonSerializer.Serialize(new { action = "purchaseError", error = result.Error ?? "שגיאה" });
                Dispatcher.Invoke(() => PaymentWebView.CoreWebView2.PostWebMessageAsJson(errorMsg));
            }
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Failed to create pending purchase");
            var errorMsg = JsonSerializer.Serialize(new { action = "purchaseError", error = "שגיאה ביצירת רכישה" });
            Dispatcher.Invoke(() => PaymentWebView.CoreWebView2.PostWebMessageAsJson(errorMsg));
        }
    }

    private async Task HandlePaymentSuccessAsync(JsonElement root)
    {
        Logger.Information("Payment success received from JS");

        // The payment gateway has processed the payment.
        // We wait for the Firebase callback to update the purchase status.
        // If status changes to "completed", show success to user.
        // If it doesn't arrive within 15s, poll manually.
        await Task.Delay(TimeSpan.FromSeconds(2));
        await PollPurchaseStatusAsync();
    }

    private void StartPurchaseStatusListener(string purchaseId)
    {
        _statusListener?.Stop();
        _statusListener = _firebase.DbListen($"purchases/{purchaseId}/status", (eventType, data) =>
        {
            if (eventType != "put" || data == null) return;
            var status = data.Value.ValueKind == JsonValueKind.String ? data.Value.GetString() : null;

            if (status is "completed" or "approved")
            {
                Logger.Information("Purchase {Id} completed via SSE", purchaseId);
                Dispatcher.Invoke(() =>
                {
                    PaymentSucceeded = true;
                    var msg = JsonSerializer.Serialize(new { action = "showSuccess" });
                    PaymentWebView.CoreWebView2.PostWebMessageAsJson(msg);
                });
            }
        });
    }

    private async Task PollPurchaseStatusAsync()
    {
        if (string.IsNullOrEmpty(_purchaseId)) return;

        for (int i = 0; i < 10; i++)
        {
            await Task.Delay(TimeSpan.FromSeconds(2));
            var result = await _firebase.DbGetAsync($"purchases/{_purchaseId}");
            if (result.Success && result.Data is JsonElement data && data.ValueKind == JsonValueKind.Object)
            {
                var status = data.TryGetProperty("status", out var s) ? s.GetString() : null;
                if (status is "completed" or "approved")
                {
                    Logger.Information("Purchase {Id} confirmed via polling", _purchaseId);
                    Dispatcher.Invoke(() =>
                    {
                        PaymentSucceeded = true;
                        var msg = JsonSerializer.Serialize(new { action = "showSuccess" });
                        PaymentWebView.CoreWebView2.PostWebMessageAsJson(msg);
                    });
                    return;
                }
            }
        }

        Logger.Warning("Purchase status polling timed out for {Id}", _purchaseId);
    }

    private void OnClosed(object? sender, EventArgs e)
    {
        _statusListener?.Stop();
        _server?.Stop();
        _server?.Dispose();
    }

    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        PaymentSucceeded = false;
        Close();
    }
}
