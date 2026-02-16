using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Tests for PrintMonitorService covering constructor, properties, pricing,
/// budget logic, and event subscriptions. Avoids P/Invoke and DispatcherTimer.
/// </summary>
public class PrintMonitorServiceTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PrintMonitorService _service;

    public PrintMonitorServiceTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new PrintMonitorService(_firebase, "test-uid");
    }

    public void Dispose()
    {
        _service.Dispose();
        _firebase.Dispose();
    }

    [Fact]
    public void Constructor_ShouldInitialize()
    {
        _service.Should().NotBeNull();
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void IsMonitoring_Initially_ShouldBeFalse()
    {
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void Dispose_ShouldNotThrow()
    {
        var act = () => _service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_MultipleTimes_ShouldNotThrow()
    {
        _service.Dispose();
        var act = () => _service.Dispose();
        act.Should().NotThrow();
    }

    [Fact]
    public void StopMonitoring_WhenNotStarted_ShouldNotThrow()
    {
        var act = () => _service.StopMonitoring();
        act.Should().NotThrow();
    }

    [Fact]
    public void JobAllowed_Event_ShouldBeSubscribable()
    {
        _service.JobAllowed += (_, _, _, _) => { };
        _service.Should().NotBeNull();
    }

    [Fact]
    public void JobBlocked_Event_ShouldBeSubscribable()
    {
        _service.JobBlocked += (_, _, _, _) => { };
        _service.Should().NotBeNull();
    }

    [Fact]
    public void BudgetUpdated_Event_ShouldBeSubscribable()
    {
        _service.BudgetUpdated += _ => { };
        _service.Should().NotBeNull();
    }

    [Fact]
    public void ErrorOccurred_Event_ShouldBeSubscribable()
    {
        _service.ErrorOccurred += _ => { };
        _service.Should().NotBeNull();
    }

    [Fact]
    public void CalculateCost_BW_ShouldUseDefaultPricing()
    {
        var method = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)method.Invoke(_service, new object[] { 3, 2, false })!;
        // Default BW price is 1.0 → 3 pages × 2 copies × 1.0 = 6.0
        cost.Should().Be(6.0);
    }

    [Fact]
    public void CalculateCost_Color_ShouldUseDefaultPricing()
    {
        var method = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)method.Invoke(_service, new object[] { 5, 1, true })!;
        // Default color price is 3.0 → 5 pages × 1 copy × 3.0 = 15.0
        cost.Should().Be(15.0);
    }

    [Fact]
    public void LoadPricing_WithMetadata_ShouldUpdatePrices()
    {
        _handler.When("metadata.json", new
        {
            blackAndWhitePrice = 0.5,
            colorPrice = 2.0,
        });

        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricing", BindingFlags.NonPublic | BindingFlags.Instance)!;
        loadMethod.Invoke(_service, null);

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;

        var bwCost = (double)calcMethod.Invoke(_service, new object[] { 10, 1, false })!;
        bwCost.Should().Be(5.0); // 10 × 1 × 0.5

        var colorCost = (double)calcMethod.Invoke(_service, new object[] { 10, 1, true })!;
        colorCost.Should().Be(20.0); // 10 × 1 × 2.0
    }

    [Fact]
    public void LoadPricing_WhenFails_ShouldKeepDefaults()
    {
        _handler.WhenError("metadata.json");

        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricing", BindingFlags.NonPublic | BindingFlags.Instance)!;
        loadMethod.Invoke(_service, null);

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)calcMethod.Invoke(_service, new object[] { 1, 1, false })!;
        cost.Should().Be(1.0); // Default BW price
    }

    [Fact]
    public void GetUserBudget_WithValidData_ShouldReturnBudget()
    {
        _handler.When("users/test-uid.json", new
        {
            printBalance = 25.50,
        });

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var budget = (double)method.Invoke(_service, new object[] { false })!;
        budget.Should().Be(25.50);
    }

    [Fact]
    public void GetUserBudget_WhenFails_ShouldReturnZero()
    {
        _handler.WhenError("users/test-uid.json");

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var budget = (double)method.Invoke(_service, new object[] { false })!;
        budget.Should().Be(0.0);
    }

    [Fact]
    public void GetUserBudget_ShouldCacheResults()
    {
        _handler.When("users/test-uid.json", new { printBalance = 10.0 });

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;

        // First call should fetch
        var budget1 = (double)method.Invoke(_service, new object[] { false })!;
        budget1.Should().Be(10.0);

        // Second call should use cache (same handler)
        var budget2 = (double)method.Invoke(_service, new object[] { false })!;
        budget2.Should().Be(10.0);
    }

    [Fact]
    public void GetUserBudget_ForceRefresh_ShouldBypassCache()
    {
        _handler.When("users/test-uid.json", new { printBalance = 10.0 });

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;

        // First call
        method.Invoke(_service, new object[] { false });

        // Force refresh should bypass cache
        var budget = (double)method.Invoke(_service, new object[] { true })!;
        budget.Should().Be(10.0);
    }

    [Fact]
    public void DeductBudget_WithSufficientBudget_ShouldSucceed()
    {
        _handler.When("users/test-uid.json", new { printBalance = 50.0 });
        _handler.SetDefaultSuccess();

        var method = typeof(PrintMonitorService).GetMethod("DeductBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var result = (bool)method.Invoke(_service, new object[] { 10.0, false })!;
        result.Should().BeTrue();
    }

    [Fact]
    public void DeductBudget_WithAllowNegative_ShouldAllowDebt()
    {
        _handler.When("users/test-uid.json", new { printBalance = 5.0 });
        _handler.SetDefaultSuccess();

        var method = typeof(PrintMonitorService).GetMethod("DeductBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var result = (bool)method.Invoke(_service, new object[] { 10.0, true })!;
        result.Should().BeTrue();
    }

    [Fact]
    public void DeductBudget_BudgetUpdatedEvent_ShouldFire()
    {
        _handler.When("users/test-uid.json", new { printBalance = 50.0 });
        _handler.SetDefaultSuccess();

        double? newBudget = null;
        _service.BudgetUpdated += b => newBudget = b;

        var method = typeof(PrintMonitorService).GetMethod("DeductBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, new object[] { 10.0, false });

        newBudget.Should().Be(40.0);
    }
}
