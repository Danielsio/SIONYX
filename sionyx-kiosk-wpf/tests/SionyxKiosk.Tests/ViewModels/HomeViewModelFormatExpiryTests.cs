using SionyxKiosk.ViewModels;
using Xunit;

namespace SionyxKiosk.Tests.ViewModels;

public class HomeViewModelFormatExpiryTests
{
    [Fact]
    public void FormatExpiry_Null_WithTime_ReturnsUnlimited()
    {
        Assert.Equal("ללא הגבלה", HomeViewModel.FormatExpiry(null, 3600));
    }

    [Fact]
    public void FormatExpiry_Null_NoTime_ReturnsNone()
    {
        Assert.Equal("אין", HomeViewModel.FormatExpiry(null, 0));
    }

    [Fact]
    public void FormatExpiry_Empty_WithTime_ReturnsUnlimited()
    {
        Assert.Equal("ללא הגבלה", HomeViewModel.FormatExpiry("", 3600));
    }

    [Fact]
    public void FormatExpiry_Empty_NoTime_ReturnsNone()
    {
        Assert.Equal("אין", HomeViewModel.FormatExpiry("", 0));
    }

    [Fact]
    public void FormatExpiry_InvalidDate_WithTime_ReturnsUnlimited()
    {
        Assert.Equal("ללא הגבלה", HomeViewModel.FormatExpiry("not-a-date", 3600));
    }

    [Fact]
    public void FormatExpiry_InvalidDate_NoTime_ReturnsNone()
    {
        Assert.Equal("אין", HomeViewModel.FormatExpiry("not-a-date", 0));
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
    public void FormatExpiry_ThreeDaysOut_ReturnsExactDate()
    {
        var future = DateTime.Now.AddDays(3).AddMinutes(1);
        var result = HomeViewModel.FormatExpiry(future.ToString("o"));
        Assert.Equal(future.ToString("dd/MM/yyyy HH:mm"), result);
    }

    [Fact]
    public void FormatExpiry_TenDaysOut_ReturnsExactDate()
    {
        var future = DateTime.Now.AddDays(10).AddMinutes(1);
        var result = HomeViewModel.FormatExpiry(future.ToString("o"));
        Assert.Equal(future.ToString("dd/MM/yyyy HH:mm"), result);
    }

    [Fact]
    public void FormatExpiry_TwoDaysExact_ReturnsExactDate()
    {
        var future = DateTime.Now.AddDays(2).AddMinutes(1);
        var result = HomeViewModel.FormatExpiry(future.ToString("o"));
        Assert.Equal(future.ToString("dd/MM/yyyy HH:mm"), result);
    }

    [Fact]
    public void FormatExpiry_TwentyHours_ReturnsExactDate()
    {
        var future = DateTime.Now.AddHours(20).AddSeconds(30);
        var result = HomeViewModel.FormatExpiry(future.ToString("o"));
        Assert.Equal(future.ToString("dd/MM/yyyy HH:mm"), result);
    }

    [Fact]
    public void FormatExpiry_OneHour_ReturnsExactDate()
    {
        var future = DateTime.Now.AddHours(1).AddMinutes(5);
        var result = HomeViewModel.FormatExpiry(future.ToString("o"));
        Assert.Equal(future.ToString("dd/MM/yyyy HH:mm"), result);
    }

    [Fact]
    public void FormatExpiry_ThirtyMinutes_ReturnsExactDate()
    {
        var future = DateTime.Now.AddMinutes(31);
        var result = HomeViewModel.FormatExpiry(future.ToString("o"));
        Assert.Equal(future.ToString("dd/MM/yyyy HH:mm"), result);
    }

    [Fact]
    public void FormatExpiry_FiveMinutes_ReturnsExactDate()
    {
        var future = DateTime.Now.AddMinutes(6);
        var result = HomeViewModel.FormatExpiry(future.ToString("o"));
        Assert.Equal(future.ToString("dd/MM/yyyy HH:mm"), result);
    }

    [Fact]
    public void FormatExpiry_JustExpired_ReturnsExpired()
    {
        var justPast = DateTime.Now.AddSeconds(-5).ToString("o");
        Assert.Equal("פג תוקף", HomeViewModel.FormatExpiry(justPast));
    }
}
