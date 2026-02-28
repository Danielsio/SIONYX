using System.Collections.ObjectModel;
using System.Collections.Specialized;
using CommunityToolkit.Mvvm.ComponentModel;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

public partial class PrintHistoryViewModel : ObservableObject, IDisposable
{
    private readonly PrintHistoryService _history;

    [ObservableProperty] private int _totalPages;
    [ObservableProperty] private double _totalCost;
    [ObservableProperty] private int _approvedCount;
    [ObservableProperty] private int _deniedCount;

    public ObservableCollection<PrintJobRecord> Jobs => _history.Jobs;

    public bool HasJobs => Jobs.Count > 0;

    public PrintHistoryViewModel(PrintHistoryService history)
    {
        _history = history;
        RefreshStats();

        _history.Jobs.CollectionChanged += OnJobsChanged;
    }

    private void OnJobsChanged(object? sender, NotifyCollectionChangedEventArgs e)
    {
        RefreshStats();
        OnPropertyChanged(nameof(HasJobs));
    }

    private void RefreshStats()
    {
        TotalPages = _history.TotalPages;
        TotalCost = _history.TotalCost;
        ApprovedCount = _history.ApprovedCount;
        DeniedCount = _history.DeniedCount;
    }

    public void Dispose()
    {
        _history.Jobs.CollectionChanged -= OnJobsChanged;
    }
}
