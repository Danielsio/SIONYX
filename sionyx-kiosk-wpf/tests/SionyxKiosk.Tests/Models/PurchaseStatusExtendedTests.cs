using FluentAssertions;
using SionyxKiosk.Models;

namespace SionyxKiosk.Tests.Models;

public class PurchaseStatusExtendedTests
{
    // ==================== HEBREW LABELS ====================

    [Fact]
    public void ToHebrewLabel_Pending_ShouldReturnHebrew()
    {
        PurchaseStatus.Pending.ToHebrewLabel().Should().Be("ממתין");
    }

    [Fact]
    public void ToHebrewLabel_Completed_ShouldReturnHebrew()
    {
        PurchaseStatus.Completed.ToHebrewLabel().Should().Be("הושלם");
    }

    [Fact]
    public void ToHebrewLabel_Failed_ShouldReturnHebrew()
    {
        PurchaseStatus.Failed.ToHebrewLabel().Should().Be("נכשל");
    }

    // ==================== COLOR NAMES ====================

    [Fact]
    public void ToColorName_Pending_ShouldBeProcessing()
    {
        PurchaseStatus.Pending.ToColorName().Should().Be("processing");
    }

    [Fact]
    public void ToColorName_Completed_ShouldBeSuccess()
    {
        PurchaseStatus.Completed.ToColorName().Should().Be("success");
    }

    [Fact]
    public void ToColorName_Failed_ShouldBeError()
    {
        PurchaseStatus.Failed.ToColorName().Should().Be("error");
    }

    // ==================== IS FINAL ====================

    [Fact]
    public void IsFinal_Pending_ShouldBeFalse()
    {
        PurchaseStatus.Pending.IsFinal().Should().BeFalse();
    }

    [Fact]
    public void IsFinal_Completed_ShouldBeTrue()
    {
        PurchaseStatus.Completed.IsFinal().Should().BeTrue();
    }

    [Fact]
    public void IsFinal_Failed_ShouldBeTrue()
    {
        PurchaseStatus.Failed.IsFinal().Should().BeTrue();
    }

    // ==================== FROM NEDARIM STATUS ====================

    [Fact]
    public void FromNedarimStatus_Error_ShouldBeFailed()
    {
        PurchaseStatusExtensions.FromNedarimStatus("Error").Should().Be(PurchaseStatus.Failed);
    }

    [Fact]
    public void FromNedarimStatus_Success_ShouldBeCompleted()
    {
        PurchaseStatusExtensions.FromNedarimStatus("Success").Should().Be(PurchaseStatus.Completed);
    }

    [Fact]
    public void FromNedarimStatus_AnyOther_ShouldBeCompleted()
    {
        PurchaseStatusExtensions.FromNedarimStatus("OK").Should().Be(PurchaseStatus.Completed);
    }

    [Fact]
    public void FromNedarimStatus_Null_ShouldBeCompleted()
    {
        PurchaseStatusExtensions.FromNedarimStatus(null).Should().Be(PurchaseStatus.Completed);
    }

    // ==================== PARSE ====================

    [Fact]
    public void Parse_Completed_ShouldReturnCompleted()
    {
        PurchaseStatusExtensions.Parse("completed").Should().Be(PurchaseStatus.Completed);
    }

    [Fact]
    public void Parse_Failed_ShouldReturnFailed()
    {
        PurchaseStatusExtensions.Parse("failed").Should().Be(PurchaseStatus.Failed);
    }

    [Fact]
    public void Parse_Pending_ShouldReturnPending()
    {
        PurchaseStatusExtensions.Parse("pending").Should().Be(PurchaseStatus.Pending);
    }

    [Fact]
    public void Parse_Unknown_ShouldDefaultToPending()
    {
        PurchaseStatusExtensions.Parse("unknown").Should().Be(PurchaseStatus.Pending);
    }

    [Fact]
    public void Parse_Null_ShouldDefaultToPending()
    {
        PurchaseStatusExtensions.Parse(null).Should().Be(PurchaseStatus.Pending);
    }

    [Fact]
    public void Parse_CaseInsensitive_ShouldWork()
    {
        PurchaseStatusExtensions.Parse("COMPLETED").Should().Be(PurchaseStatus.Completed);
        PurchaseStatusExtensions.Parse("Failed").Should().Be(PurchaseStatus.Failed);
    }

    // ==================== TO DB VALUE ====================

    [Fact]
    public void ToDbValue_ShouldReturnLowercase()
    {
        PurchaseStatus.Pending.ToDbValue().Should().Be("pending");
        PurchaseStatus.Completed.ToDbValue().Should().Be("completed");
        PurchaseStatus.Failed.ToDbValue().Should().Be("failed");
    }
}

public class PurchaseModelExtendedTests
{
    [Fact]
    public void Purchase_DefaultValues_ShouldHaveCorrectDefaults()
    {
        var purchase = new Purchase();
        purchase.Id.Should().BeEmpty();
        purchase.UserId.Should().BeEmpty();
        purchase.PackageId.Should().BeEmpty();
        purchase.PackageName.Should().BeEmpty();
        purchase.Minutes.Should().Be(0);
        purchase.Prints.Should().Be(0);
        purchase.PrintBudget.Should().Be(0);
        purchase.ValidityDays.Should().Be(0);
        purchase.Amount.Should().Be(0);
        purchase.Status.Should().Be("pending");
        purchase.CreatedAt.Should().BeEmpty();
        purchase.UpdatedAt.Should().BeEmpty();
    }

    [Fact]
    public void Purchase_AllProperties_ShouldRoundtrip()
    {
        var purchase = new Purchase
        {
            Id = "p1",
            UserId = "u1",
            PackageId = "pkg1",
            PackageName = "Premium",
            Minutes = 120,
            Prints = 20,
            PrintBudget = 20.0,
            ValidityDays = 30,
            Amount = 49.90,
            Status = "completed",
            CreatedAt = "2026-01-01",
            UpdatedAt = "2026-01-15",
        };

        purchase.Id.Should().Be("p1");
        purchase.UserId.Should().Be("u1");
        purchase.PackageId.Should().Be("pkg1");
        purchase.PackageName.Should().Be("Premium");
        purchase.Minutes.Should().Be(120);
        purchase.Prints.Should().Be(20);
        purchase.PrintBudget.Should().Be(20.0);
        purchase.ValidityDays.Should().Be(30);
        purchase.Amount.Should().Be(49.90);
        purchase.Status.Should().Be("completed");
    }
}
