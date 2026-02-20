using SionyxKiosk.Models;
using Xunit;

namespace SionyxKiosk.Tests.Models;

public class PackageComputedPropertyTests
{
    [Fact]
    public void HasDiscount_ZeroPercent_ReturnsFalse()
    {
        var pkg = new Package { DiscountPercent = 0 };
        Assert.False(pkg.HasDiscount);
    }

    [Fact]
    public void HasDiscount_PositivePercent_ReturnsTrue()
    {
        var pkg = new Package { DiscountPercent = 15 };
        Assert.True(pkg.HasDiscount);
    }

    [Fact]
    public void FinalPrice_NoDiscount_EqualsPrice()
    {
        var pkg = new Package { Price = 100, DiscountPercent = 0 };
        Assert.Equal(100, pkg.FinalPrice);
    }

    [Fact]
    public void FinalPrice_WithDiscount_CalculatesCorrectly()
    {
        var pkg = new Package { Price = 200, DiscountPercent = 25 };
        Assert.Equal(150, pkg.FinalPrice);
    }

    [Fact]
    public void FinalPrice_RoundsToTwoDecimals()
    {
        var pkg = new Package { Price = 100, DiscountPercent = 33 };
        Assert.Equal(67, pkg.FinalPrice);
    }

    [Fact]
    public void Savings_NoDiscount_ReturnsZero()
    {
        var pkg = new Package { Price = 100, DiscountPercent = 0 };
        Assert.Equal(0, pkg.Savings);
    }

    [Fact]
    public void Savings_WithDiscount_CalculatesCorrectly()
    {
        var pkg = new Package { Price = 200, DiscountPercent = 10 };
        Assert.Equal(20, pkg.Savings);
    }

    [Fact]
    public void DisplayPrice_NoDiscount_ReturnsPrice()
    {
        var pkg = new Package { Price = 50, DiscountPercent = 0 };
        Assert.Equal(50, pkg.DisplayPrice);
    }

    [Fact]
    public void DisplayPrice_WithDiscount_ReturnsFinalPrice()
    {
        var pkg = new Package { Price = 100, DiscountPercent = 15 };
        Assert.Equal(pkg.FinalPrice, pkg.DisplayPrice);
    }

    [Theory]
    [InlineData(0, "ללא הגבלה")]
    [InlineData(1, "יום אחד")]
    [InlineData(7, "שבוע")]
    [InlineData(14, "שבועיים")]
    [InlineData(30, "חודש")]
    [InlineData(60, "חודשיים")]
    [InlineData(90, "3 חודשים")]
    [InlineData(365, "שנה")]
    [InlineData(45, "45 ימים")]
    [InlineData(3, "3 ימים")]
    [InlineData(180, "180 ימים")]
    public void ValidityDisplay_MapsCorrectly(int days, string expected)
    {
        var pkg = new Package { ValidityDays = days };
        Assert.Equal(expected, pkg.ValidityDisplay);
    }

    [Fact]
    public void DefaultValues_AreCorrect()
    {
        var pkg = new Package();
        Assert.Equal("", pkg.Id);
        Assert.Equal("", pkg.Name);
        Assert.Equal(0, pkg.Price);
        Assert.Equal(0, pkg.Minutes);
        Assert.Equal(0, pkg.Prints);
        Assert.Equal(0, pkg.DiscountPercent);
        Assert.Equal(0, pkg.ValidityDays);
        Assert.False(pkg.IsFeatured);
        Assert.False(pkg.HasDiscount);
        Assert.Equal(0, pkg.DisplayPrice);
        Assert.Equal("ללא הגבלה", pkg.ValidityDisplay);
    }

    [Fact]
    public void FullDiscount_PriceIsZero()
    {
        var pkg = new Package { Price = 100, DiscountPercent = 100 };
        Assert.Equal(0, pkg.FinalPrice);
        Assert.Equal(100, pkg.Savings);
        Assert.Equal(0, pkg.DisplayPrice);
    }

    [Fact]
    public void Purchase_DefaultValues_AreCorrect()
    {
        var purchase = new Purchase();
        Assert.Equal("", purchase.Id);
        Assert.Equal("", purchase.UserId);
        Assert.Equal("pending", purchase.Status);
        Assert.Equal(0, purchase.Amount);
        Assert.Equal(0, purchase.Minutes);
    }
}
