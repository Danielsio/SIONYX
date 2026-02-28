namespace SionyxKiosk.Models;

/// <summary>
/// In-memory print job record. Session-scoped — cleared on logout.
/// </summary>
public class PrintJobRecord
{
    public string DocumentName { get; set; } = "";
    public int Pages { get; set; }
    public int Copies { get; set; }
    public bool IsColor { get; set; }
    public double Cost { get; set; }
    public string Status { get; set; } = "approved"; // "approved" | "denied"
    public double RemainingAfter { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.Now;

    public string StatusDisplay => Status == "approved" ? "אושר" : "נדחה";
    public string StatusIcon => Status == "approved" ? "\u2705" : "\u274C";
    public string ColorMode => IsColor ? "צבעוני" : "שחור-לבן";
    public string TimeDisplay => Timestamp.ToString("HH:mm");
    public string DateDisplay => Timestamp.ToString("dd/MM/yyyy");
    public string FullDateDisplay => $"{DateDisplay} {TimeDisplay}";
    public string PagesDisplay => Pages == 1 ? "עמוד 1" : $"{Pages} עמודים";
    public string CostDisplay => $"₪{Cost:F2}";
}
