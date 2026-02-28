using FluentAssertions;
using SionyxKiosk.Models;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class PrintHistoryServiceTests
{
    [Fact]
    public void NewService_HasEmptyJobs()
    {
        var service = new PrintHistoryService();
        service.Jobs.Should().BeEmpty();
        service.TotalPages.Should().Be(0);
        service.TotalCost.Should().Be(0);
        service.ApprovedCount.Should().Be(0);
        service.DeniedCount.Should().Be(0);
    }

    [Fact]
    public void Clear_EmptyService_DoesNotThrow()
    {
        var service = new PrintHistoryService();
        var act = () => service.Clear();
        act.Should().NotThrow();
    }

    [Fact]
    public void TotalPages_CalculatesCorrectly()
    {
        var service = new PrintHistoryService();
        service.Jobs.Add(new PrintJobRecord { Pages = 5, Copies = 2 });
        service.Jobs.Add(new PrintJobRecord { Pages = 3, Copies = 1 });
        service.TotalPages.Should().Be(13); // 5*2 + 3*1
    }

    [Fact]
    public void TotalCost_OnlyCountsApproved()
    {
        var service = new PrintHistoryService();
        service.Jobs.Add(new PrintJobRecord { Cost = 10.0, Status = "approved" });
        service.Jobs.Add(new PrintJobRecord { Cost = 5.0, Status = "denied" });
        service.Jobs.Add(new PrintJobRecord { Cost = 7.5, Status = "approved" });
        service.TotalCost.Should().Be(17.5);
    }

    [Fact]
    public void ApprovedCount_IsCorrect()
    {
        var service = new PrintHistoryService();
        service.Jobs.Add(new PrintJobRecord { Status = "approved" });
        service.Jobs.Add(new PrintJobRecord { Status = "denied" });
        service.Jobs.Add(new PrintJobRecord { Status = "approved" });
        service.ApprovedCount.Should().Be(2);
    }

    [Fact]
    public void DeniedCount_IsCorrect()
    {
        var service = new PrintHistoryService();
        service.Jobs.Add(new PrintJobRecord { Status = "approved" });
        service.Jobs.Add(new PrintJobRecord { Status = "denied" });
        service.Jobs.Add(new PrintJobRecord { Status = "denied" });
        service.DeniedCount.Should().Be(2);
    }

    [Fact]
    public void Jobs_IsObservable()
    {
        var service = new PrintHistoryService();
        int changeCount = 0;
        service.Jobs.CollectionChanged += (_, _) => changeCount++;

        service.Jobs.Add(new PrintJobRecord { DocumentName = "test.pdf" });
        changeCount.Should().Be(1);

        service.Jobs.Clear();
        changeCount.Should().Be(2);
    }

    [Fact]
    public void EmptyService_AllStatsZero()
    {
        var service = new PrintHistoryService();
        service.TotalPages.Should().Be(0);
        service.TotalCost.Should().Be(0);
        service.ApprovedCount.Should().Be(0);
        service.DeniedCount.Should().Be(0);
    }

    [Fact]
    public void MixedJobs_StatsCorrect()
    {
        var service = new PrintHistoryService();
        service.Jobs.Add(new PrintJobRecord
        {
            DocumentName = "Doc1.pdf", Pages = 5, Copies = 1,
            Cost = 5.0, Status = "approved"
        });
        service.Jobs.Add(new PrintJobRecord
        {
            DocumentName = "Doc2.pdf", Pages = 10, Copies = 2,
            Cost = 20.0, Status = "denied"
        });
        service.Jobs.Add(new PrintJobRecord
        {
            DocumentName = "Doc3.pdf", Pages = 1, Copies = 1,
            Cost = 1.0, Status = "approved"
        });

        service.TotalPages.Should().Be(26); // 5*1 + 10*2 + 1*1
        service.TotalCost.Should().Be(6.0); // 5.0 + 1.0 (only approved)
        service.ApprovedCount.Should().Be(2);
        service.DeniedCount.Should().Be(1);
    }
}
