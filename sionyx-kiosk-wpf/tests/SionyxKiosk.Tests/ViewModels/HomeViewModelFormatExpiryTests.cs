using SionyxKiosk.ViewModels;
using Xunit;

namespace SionyxKiosk.Tests.ViewModels;

public class HomeViewModelFormatExpiryTests
{
    [Fact]
    public void FormatExpiry_Null_ReturnsUnlimited()
    {
        Assert.Equal("ללא הגבלה", HomeViewModel.FormatExpiry(null));
    }

    [Fact]
    public void FormatExpiry_Empty_ReturnsUnlimited()
    {
        Assert.Equal("ללא הגבלה", HomeViewModel.FormatExpiry(""));
    }

    [Fact]
    public void FormatExpiry_InvalidDate_ReturnsUnlimited()
    {
        Assert.Equal("ללא הגבלה", HomeViewModel.FormatExpiry("not-a-date"));
    }

    [Fact]
    public void FormatExpiry_PastDate_ReturnsExpired()
    {
        var past = DateTime.Now.AddHours(-1).ToString("o");
        Assert.Equal("פג תוקף", HomeViewModel.FormatExpiry(past));
    }

    [Fact]
    public void FormatExpiry_FarPast_ReturnsExpired()
    {
        var past = DateTime.Now.AddDays(-30).ToString("o");
        Assert.Equal("פג תוקף", HomeViewModel.FormatExpiry(past));
    }

    [Fact]
    public void FormatExpiry_ThreeDaysOut_ReturnsDays()
    {
        var future = DateTime.Now.AddDays(3).AddMinutes(1).ToString("o");
        var result = HomeViewModel.FormatExpiry(future);
        Assert.Equal("3 ימים", result);
    }

    [Fact]
    public void FormatExpiry_TenDaysOut_ReturnsDays()
    {
        var future = DateTime.Now.AddDays(10).AddMinutes(1).ToString("o");
        var result = HomeViewModel.FormatExpiry(future);
        Assert.Equal("10 ימים", result);
    }

    [Fact]
    public void FormatExpiry_TwoDaysExact_ReturnsDays()
    {
        var future = DateTime.Now.AddDays(2).AddMinutes(1).ToString("o");
        var result = HomeViewModel.FormatExpiry(future);
        Assert.Equal("2 ימים", result);
    }

    [Fact]
    public void FormatExpiry_TwentyHours_ReturnsHours()
    {
        var future = DateTime.Now.AddHours(20).AddSeconds(30).ToString("o");
        var result = HomeViewModel.FormatExpiry(future);
        Assert.EndsWith("שעות", result);
        Assert.Contains("20", result);
    }

    [Fact]
    public void FormatExpiry_OneHour_ReturnsHours()
    {
        var future = DateTime.Now.AddHours(1).AddMinutes(5).ToString("o");
        var result = HomeViewModel.FormatExpiry(future);
        Assert.EndsWith("שעות", result);
    }

    [Fact]
    public void FormatExpiry_ThirtyMinutes_ReturnsMinutes()
    {
        var future = DateTime.Now.AddMinutes(31).ToString("o");
        var result = HomeViewModel.FormatExpiry(future);
        Assert.EndsWith("דקות", result);
        Assert.Contains("30", result);
    }

    [Fact]
    public void FormatExpiry_FiveMinutes_ReturnsMinutes()
    {
        var future = DateTime.Now.AddMinutes(6).ToString("o");
        var result = HomeViewModel.FormatExpiry(future);
        Assert.EndsWith("דקות", result);
        Assert.Contains("5", result);
    }

    [Fact]
    public void FormatExpiry_JustExpired_ReturnsExpired()
    {
        var justPast = DateTime.Now.AddSeconds(-5).ToString("o");
        Assert.Equal("פג תוקף", HomeViewModel.FormatExpiry(justPast));
    }
}
