namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Resolves the callback URL sent to the Nedarim gateway with a payment.
/// </summary>
public static class PaymentCallback
{
    /// <summary>
    /// Configured URL → use it (e.g. the Worker, server-authoritative).
    /// "none" or unset → empty string, so the gateway falls back to the
    /// callback configured on the mosad account (most secure: no callback
    /// secret ever lives on the kiosk). Unset must NOT point anywhere else:
    /// the old fallback hit the deleted Cloud Function (404), which charged
    /// the card but never credited the purchase.
    /// </summary>
    public static string Resolve(string? configured)
    {
        if (string.IsNullOrWhiteSpace(configured))
            return "";
        var trimmed = configured.Trim();
        return string.Equals(trimmed, "none", StringComparison.OrdinalIgnoreCase) ? "" : trimmed;
    }
}
