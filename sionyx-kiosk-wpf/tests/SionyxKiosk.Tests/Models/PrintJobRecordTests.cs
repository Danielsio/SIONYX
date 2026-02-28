using FluentAssertions;
using SionyxKiosk.Models;

namespace SionyxKiosk.Tests.Models;

public class PrintJobRecordTests
{
    [Fact]
    public void DefaultValues_AreCorrect()
    {
        var record = new PrintJobRecord();

        record.DocumentName.Should().Be("");
        record.Pages.Should().Be(0);
        record.Copies.Should().Be(0);
        record.IsColor.Should().BeFalse();
        record.Cost.Should().Be(0);
        record.Status.Should().Be("approved");
        record.RemainingAfter.Should().Be(0);
        record.Timestamp.Should().BeCloseTo(DateTime.Now, TimeSpan.FromSeconds(5));
    }

    [Fact]
    public void StatusDisplay_Approved_ReturnsHebrew()
    {
        var record = new PrintJobRecord { Status = "approved" };
        record.StatusDisplay.Should().Be("אושר");
    }

    [Fact]
    public void StatusDisplay_Denied_ReturnsHebrew()
    {
        var record = new PrintJobRecord { Status = "denied" };
        record.StatusDisplay.Should().Be("נדחה");
    }

    [Fact]
    public void StatusIcon_Approved_ReturnsCheckmark()
    {
        var record = new PrintJobRecord { Status = "approved" };
        record.StatusIcon.Should().Be("\u2705");
    }

    [Fact]
    public void StatusIcon_Denied_ReturnsCross()
    {
        var record = new PrintJobRecord { Status = "denied" };
        record.StatusIcon.Should().Be("\u274C");
    }

    [Fact]
    public void ColorMode_BW_ReturnsHebrew()
    {
        var record = new PrintJobRecord { IsColor = false };
        record.ColorMode.Should().Be("שחור-לבן");
    }

    [Fact]
    public void ColorMode_Color_ReturnsHebrew()
    {
        var record = new PrintJobRecord { IsColor = true };
        record.ColorMode.Should().Be("צבעוני");
    }

    [Fact]
    public void PagesDisplay_SinglePage()
    {
        var record = new PrintJobRecord { Pages = 1 };
        record.PagesDisplay.Should().Be("עמוד 1");
    }

    [Fact]
    public void PagesDisplay_MultiplePages()
    {
        var record = new PrintJobRecord { Pages = 5 };
        record.PagesDisplay.Should().Be("5 עמודים");
    }

    [Fact]
    public void CostDisplay_FormatsCorrectly()
    {
        var record = new PrintJobRecord { Cost = 12.5 };
        record.CostDisplay.Should().Be("₪12.50");
    }

    [Fact]
    public void TimeDisplay_FormatsCorrectly()
    {
        var record = new PrintJobRecord { Timestamp = new DateTime(2026, 2, 27, 14, 30, 0) };
        record.TimeDisplay.Should().Be("14:30");
    }

    [Fact]
    public void DateDisplay_FormatsCorrectly()
    {
        var record = new PrintJobRecord { Timestamp = new DateTime(2026, 2, 27, 14, 30, 0) };
        record.DateDisplay.Should().Be("27/02/2026");
    }

    [Fact]
    public void FullDateDisplay_CombinesDateAndTime()
    {
        var record = new PrintJobRecord { Timestamp = new DateTime(2026, 2, 27, 14, 30, 0) };
        record.FullDateDisplay.Should().Be("27/02/2026 14:30");
    }

    [Fact]
    public void AllProperties_CanBeSet()
    {
        var ts = new DateTime(2026, 1, 15, 10, 0, 0);
        var record = new PrintJobRecord
        {
            DocumentName = "Report.pdf",
            Pages = 10,
            Copies = 2,
            IsColor = true,
            Cost = 15.0,
            Status = "denied",
            RemainingAfter = 30.0,
            Timestamp = ts
        };

        record.DocumentName.Should().Be("Report.pdf");
        record.Pages.Should().Be(10);
        record.Copies.Should().Be(2);
        record.IsColor.Should().BeTrue();
        record.Cost.Should().Be(15.0);
        record.Status.Should().Be("denied");
        record.RemainingAfter.Should().Be(30.0);
        record.Timestamp.Should().Be(ts);
    }
}
