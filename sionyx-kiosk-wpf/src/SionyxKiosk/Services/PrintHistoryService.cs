using System.Collections.ObjectModel;
using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

/// <summary>
/// In-memory print job history. Session-scoped — all data lives in memory
/// and is cleared when the user logs out. No Firebase persistence.
/// </summary>
public class PrintHistoryService
{
    public ObservableCollection<PrintJobRecord> Jobs { get; } = new();

    public int TotalPages => Jobs.Sum(j => j.Pages * j.Copies);
    public double TotalCost => Jobs.Where(j => j.Status == "approved").Sum(j => j.Cost);
    public int ApprovedCount => Jobs.Count(j => j.Status == "approved");
    public int DeniedCount => Jobs.Count(j => j.Status == "denied");

    public void AddJob(string documentName, int pages, int copies, bool isColor,
        double cost, string status, double remainingAfter)
    {
        var job = new PrintJobRecord
        {
            DocumentName = documentName,
            Pages = pages,
            Copies = copies,
            IsColor = isColor,
            Cost = cost,
            Status = status,
            RemainingAfter = remainingAfter,
            Timestamp = DateTime.Now
        };

        System.Windows.Application.Current?.Dispatcher.Invoke(() => Jobs.Insert(0, job));
    }

    public void Clear()
    {
        System.Windows.Application.Current?.Dispatcher.Invoke(() => Jobs.Clear());
    }
}
