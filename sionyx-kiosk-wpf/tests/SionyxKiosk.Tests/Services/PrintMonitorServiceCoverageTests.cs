using System.Reflection;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

public class PrintMonitorServiceCoverageTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly PrintMonitorService _service;

    public PrintMonitorServiceCoverageTests()
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
    public void Reinitialize_ResetsState()
    {
        _service.Reinitialize("new-user");
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void Reinitialize_StopsMonitoringFirst()
    {
        _service.Reinitialize("another-user");
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void CalculateCost_SinglePageBW()
    {
        var method = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)method.Invoke(_service, new object[] { 1, 1, false })!;
        cost.Should().Be(1.0);
    }

    [Fact]
    public void CalculateCost_MultipleCopiesColor()
    {
        var method = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)method.Invoke(_service, new object[] { 10, 3, true })!;
        cost.Should().Be(90.0);
    }

    [Fact]
    public void CalculateCost_ZeroPages()
    {
        var method = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)method.Invoke(_service, new object[] { 0, 1, false })!;
        cost.Should().Be(0.0);
    }

    [Fact]
    public void CalculateCost_ZeroCopies()
    {
        var method = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)method.Invoke(_service, new object[] { 5, 0, true })!;
        cost.Should().Be(0.0);
    }

    [Fact]
    public void LoadPricing_WithPartialData_ShouldUseAvailable()
    {
        _handler.When("metadata.json", new { blackAndWhitePrice = 2.0 });
        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricing", BindingFlags.NonPublic | BindingFlags.Instance)!;
        loadMethod.Invoke(_service, null);

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var bwCost = (double)calcMethod.Invoke(_service, new object[] { 1, 1, false })!;
        bwCost.Should().Be(2.0);
    }

    [Fact]
    public void LoadPricing_EmptyObject_ShouldKeepDefaults()
    {
        _handler.When("metadata.json", new { });
        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricing", BindingFlags.NonPublic | BindingFlags.Instance)!;
        loadMethod.Invoke(_service, null);

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)calcMethod.Invoke(_service, new object[] { 1, 1, false })!;
        cost.Should().Be(1.0);
    }

    [Fact]
    public void LoadPricing_NullResponse_ShouldKeepDefaults()
    {
        _handler.WhenRaw("metadata.json", "null");
        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricing", BindingFlags.NonPublic | BindingFlags.Instance)!;
        loadMethod.Invoke(_service, null);

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)calcMethod.Invoke(_service, new object[] { 1, 1, true })!;
        cost.Should().Be(3.0);
    }

    [Fact]
    public void GetUserBudget_NoPrintBalance_ShouldReturnZero()
    {
        _handler.When("users/test-uid.json", new { name = "test" });

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var budget = (double)method.Invoke(_service, new object[] { false })!;
        budget.Should().Be(0.0);
    }

    [Fact]
    public void GetUserBudget_NullResponse_ShouldReturnZero()
    {
        _handler.WhenRaw("users/test-uid.json", "null");

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var budget = (double)method.Invoke(_service, new object[] { false })!;
        budget.Should().Be(0.0);
    }

    [Fact]
    public void GetUserBudget_CachingWorks()
    {
        _handler.When("users/test-uid.json", new { printBalance = 42.0 });

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;

        var b1 = (double)method.Invoke(_service, new object[] { false })!;
        b1.Should().Be(42.0);

        _handler.ClearHandlers();
        _handler.WhenError("users/test-uid.json");

        var b2 = (double)method.Invoke(_service, new object[] { false })!;
        b2.Should().Be(42.0);
    }

    [Fact]
    public void DeductBudget_WhenDbFails_ShouldReturnFalse()
    {
        _handler.WhenError("users/test-uid.json");

        var method = typeof(PrintMonitorService).GetMethod("DeductBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var result = (bool)method.Invoke(_service, new object[] { 10.0, false })!;
        result.Should().BeFalse();
    }

    [Fact]
    public void DeductBudget_WithoutAllowNegative_ShouldClampToZero()
    {
        _handler.When("users/test-uid.json", new { printBalance = 5.0 });
        _handler.SetDefaultSuccess();

        double? budgetReceived = null;
        _service.BudgetUpdated += b => budgetReceived = b;

        var method = typeof(PrintMonitorService).GetMethod("DeductBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        method.Invoke(_service, new object[] { 10.0, false });

        budgetReceived.Should().Be(0.0);
    }

    [Fact]
    public void StopMonitoring_Idempotent()
    {
        _service.StopMonitoring();
        _service.StopMonitoring();
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void Events_CanAttachMultipleHandlers()
    {
        int allowedCount = 0;
        int blockedCount = 0;
        int errorCount = 0;

        _service.JobAllowed += (_, _, _, _) => allowedCount++;
        _service.JobAllowed += (_, _, _, _) => allowedCount++;
        _service.JobBlocked += (_, _, _, _) => blockedCount++;
        _service.ErrorOccurred += _ => errorCount++;

        _service.Should().NotBeNull();
    }

    [Fact]
    public void Reinitialize_ClearsCache()
    {
        _handler.When("users/test-uid.json", new { printBalance = 100.0 });
        var getBudget = typeof(PrintMonitorService).GetMethod("GetUserBudget", BindingFlags.NonPublic | BindingFlags.Instance)!;
        getBudget.Invoke(_service, new object[] { false });

        _service.Reinitialize("other-user");

        _handler.ClearHandlers();
        _handler.When("users/other-user.json", new { printBalance = 0.0 });

        var budget = (double)getBudget.Invoke(_service, new object[] { true })!;
        budget.Should().Be(0.0);
    }
}
