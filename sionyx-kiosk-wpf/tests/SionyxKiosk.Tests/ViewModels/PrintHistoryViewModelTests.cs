using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;
using SionyxKiosk.ViewModels;

namespace SionyxKiosk.Tests.ViewModels;

public class PrintHistoryViewModelTests : IDisposable
{
    private readonly PrintHistoryService _service;
    private readonly PrintHistoryViewModel _vm;

    public PrintHistoryViewModelTests()
    {
        _service = new PrintHistoryService();
        _vm = new PrintHistoryViewModel(_service);
    }

    public void Dispose() => _vm.Dispose();

    [Fact]
    public void Constructor_InitializesWithEmptyStats()
    {
        _vm.TotalPages.Should().Be(0);
        _vm.TotalCost.Should().Be(0);
        _vm.ApprovedCount.Should().Be(0);
        _vm.DeniedCount.Should().Be(0);
        _vm.HasJobs.Should().BeFalse();
    }

    [Fact]
    public void Jobs_ReturnsSameCollectionAsService()
    {
        _vm.Jobs.Should().BeSameAs(_service.Jobs);
    }

    [Fact]
    public void AddingJob_UpdatesStats()
    {
        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 5, Copies = 1, Cost = 10.0, Status = "approved"
        });

        _vm.TotalPages.Should().Be(5);
        _vm.TotalCost.Should().Be(10.0);
        _vm.ApprovedCount.Should().Be(1);
        _vm.DeniedCount.Should().Be(0);
        _vm.HasJobs.Should().BeTrue();
    }

    [Fact]
    public void AddingDeniedJob_UpdatesDeniedCount()
    {
        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 3, Copies = 1, Cost = 6.0, Status = "denied"
        });

        _vm.DeniedCount.Should().Be(1);
        _vm.ApprovedCount.Should().Be(0);
        _vm.TotalCost.Should().Be(0); // denied jobs don't count toward cost
    }

    [Fact]
    public void ClearingJobs_ResetsStats()
    {
        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 5, Copies = 1, Cost = 10.0, Status = "approved"
        });
        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 3, Copies = 1, Cost = 6.0, Status = "denied"
        });

        _vm.HasJobs.Should().BeTrue();

        _service.Jobs.Clear();

        _vm.TotalPages.Should().Be(0);
        _vm.TotalCost.Should().Be(0);
        _vm.ApprovedCount.Should().Be(0);
        _vm.DeniedCount.Should().Be(0);
        _vm.HasJobs.Should().BeFalse();
    }

    [Fact]
    public void MultipleJobs_StatsAccumulate()
    {
        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 5, Copies = 1, Cost = 5.0, Status = "approved"
        });
        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 10, Copies = 2, Cost = 20.0, Status = "approved"
        });
        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 1, Copies = 1, Cost = 3.0, Status = "denied"
        });

        _vm.TotalPages.Should().Be(26); // 5 + 20 + 1
        _vm.TotalCost.Should().Be(25.0); // 5 + 20
        _vm.ApprovedCount.Should().Be(2);
        _vm.DeniedCount.Should().Be(1);
    }

    [Fact]
    public void PropertyChanged_FiredOnStatsUpdate()
    {
        var changedProps = new List<string>();
        _vm.PropertyChanged += (_, e) => changedProps.Add(e.PropertyName!);

        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 5, Copies = 1, Cost = 10.0, Status = "approved"
        });

        changedProps.Should().Contain("TotalPages");
        changedProps.Should().Contain("TotalCost");
        changedProps.Should().Contain("ApprovedCount");
        changedProps.Should().Contain("HasJobs");
        // DeniedCount stays 0 -> 0, so [ObservableProperty] won't fire
    }

    [Fact]
    public void PropertyChanged_DeniedCount_FiresWhenChanged()
    {
        var changedProps = new List<string>();
        _vm.PropertyChanged += (_, e) => changedProps.Add(e.PropertyName!);

        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 3, Copies = 1, Cost = 5.0, Status = "denied"
        });

        changedProps.Should().Contain("DeniedCount");
    }

    [Fact]
    public void Dispose_StopsListeningToChanges()
    {
        _vm.Dispose();

        var changedProps = new List<string>();
        _vm.PropertyChanged += (_, e) => changedProps.Add(e.PropertyName!);

        _service.Jobs.Add(new PrintJobRecord
        {
            Pages = 5, Copies = 1, Cost = 10.0, Status = "approved"
        });

        changedProps.Should().NotContain("TotalPages");
    }
}
