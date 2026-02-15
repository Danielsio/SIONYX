using FluentAssertions;
using SionyxKiosk.Models;

namespace SionyxKiosk.Tests.Infrastructure;

public class PurchaseStatusTests
{
    [Fact]
    public void ToDbValue_ShouldReturnCorrectStrings()
    {
        PurchaseStatus.Pending.ToDbValue().Should().Be("pending");
        PurchaseStatus.Completed.ToDbValue().Should().Be("completed");
        PurchaseStatus.Failed.ToDbValue().Should().Be("failed");
    }

    [Fact]
    public void ToHebrewLabel_ShouldReturnHebrewStrings()
    {
        PurchaseStatus.Pending.ToHebrewLabel().Should().NotBeNullOrWhiteSpace();
        PurchaseStatus.Completed.ToHebrewLabel().Should().NotBeNullOrWhiteSpace();
        PurchaseStatus.Failed.ToHebrewLabel().Should().NotBeNullOrWhiteSpace();
    }

    [Fact]
    public void Parse_ShouldRoundtrip()
    {
        PurchaseStatusExtensions.Parse("completed").Should().Be(PurchaseStatus.Completed);
        PurchaseStatusExtensions.Parse("failed").Should().Be(PurchaseStatus.Failed);
        PurchaseStatusExtensions.Parse("pending").Should().Be(PurchaseStatus.Pending);
        PurchaseStatusExtensions.Parse("unknown").Should().Be(PurchaseStatus.Pending);
    }

    [Fact]
    public void IsFinal_ShouldBeCorrect()
    {
        PurchaseStatus.Pending.IsFinal().Should().BeFalse();
        PurchaseStatus.Completed.IsFinal().Should().BeTrue();
        PurchaseStatus.Failed.IsFinal().Should().BeTrue();
    }
}
