using FluentAssertions;
using SionyxKiosk.Models;

namespace SionyxKiosk.Tests.Models;

public class PackageTests
{
    [Fact]
    public void Package_DefaultValues()
    {
        var pkg = new Package();
        pkg.Id.Should().BeEmpty();
        pkg.Name.Should().BeEmpty();
        pkg.Price.Should().Be(0);
        pkg.Minutes.Should().Be(0);
        pkg.Prints.Should().Be(0);
        pkg.IsFeatured.Should().BeFalse();
    }

    [Fact]
    public void Package_Properties_ShouldRoundtrip()
    {
        var pkg = new Package
        {
            Id = "pkg-001",
            Name = "חבילה בסיסית",
            Price = 15.0,
            Minutes = 60,
            Prints = 10,
            IsFeatured = true
        };

        pkg.Id.Should().Be("pkg-001");
        pkg.Name.Should().Be("חבילה בסיסית");
        pkg.Price.Should().Be(15.0);
        pkg.Minutes.Should().Be(60);
        pkg.Prints.Should().Be(10);
        pkg.IsFeatured.Should().BeTrue();
    }

    [Fact]
    public void FinalPrice_WithDiscount_ShouldCalculateCorrectly()
    {
        var pkg = new Package { Price = 100.0, DiscountPercent = 20 };
        pkg.FinalPrice.Should().Be(80.0);
    }

    [Fact]
    public void FinalPrice_WithNoDiscount_ShouldEqualPrice()
    {
        var pkg = new Package { Price = 50.0, DiscountPercent = 0 };
        pkg.FinalPrice.Should().Be(50.0);
    }

    [Fact]
    public void Savings_ShouldBeCorrect()
    {
        var pkg = new Package { Price = 100.0, DiscountPercent = 25 };
        pkg.Savings.Should().Be(25.0);
    }
}

public class PurchaseModelTests
{
    [Fact]
    public void Purchase_DefaultValues()
    {
        var purchase = new Purchase();
        purchase.Id.Should().BeEmpty();
        purchase.Status.Should().Be("pending");
        purchase.Amount.Should().Be(0);
    }

    [Fact]
    public void Purchase_Properties_ShouldRoundtrip()
    {
        var purchase = new Purchase
        {
            Id = "pur-001",
            UserId = "user-123",
            PackageId = "pkg-001",
            PackageName = "חבילה בסיסית",
            Amount = 15.0,
            Status = "completed",
            CreatedAt = "2025-01-01T12:00:00Z"
        };

        purchase.Id.Should().Be("pur-001");
        purchase.UserId.Should().Be("user-123");
        purchase.Amount.Should().Be(15.0);
        purchase.Status.Should().Be("completed");
    }
}
