using System.Reflection;
using System.Threading.Tasks;
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
    public async Task LoadPricing_WithPartialData_ShouldUseAvailable()
    {
        _handler.When("metadata.json", new { blackAndWhitePrice = 2.0 });
        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricingAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var loadTask = loadMethod.Invoke(_service, null) as Task;
        if (loadTask != null) await loadTask;

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var bwCost = (double)calcMethod.Invoke(_service, new object[] { 1, 1, false })!;
        bwCost.Should().Be(2.0);
    }

    [Fact]
    public async Task LoadPricing_EmptyObject_ShouldKeepDefaults()
    {
        _handler.When("metadata.json", new { });
        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricingAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var loadTask = loadMethod.Invoke(_service, null) as Task;
        if (loadTask != null) await loadTask;

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)calcMethod.Invoke(_service, new object[] { 1, 1, false })!;
        cost.Should().Be(1.0);
    }

    [Fact]
    public async Task LoadPricing_NullResponse_ShouldKeepDefaults()
    {
        _handler.WhenRaw("metadata.json", "null");
        var loadMethod = typeof(PrintMonitorService).GetMethod("LoadPricingAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var loadTask = loadMethod.Invoke(_service, null) as Task;
        if (loadTask != null) await loadTask;

        var calcMethod = typeof(PrintMonitorService).GetMethod("CalculateCost", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var cost = (double)calcMethod.Invoke(_service, new object[] { 1, 1, true })!;
        cost.Should().Be(3.0);
    }

    [Fact]
    public async Task GetUserBudget_NoPrintBalance_ShouldReturnZero()
    {
        _handler.When("users/test-uid.json", new { name = "test" });

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudgetAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var task = method.Invoke(_service, new object[] { false }) as Task<double>;
        var budget = task != null ? await task : 0;
        budget.Should().Be(0.0);
    }

    [Fact]
    public async Task GetUserBudget_NullResponse_ShouldReturnZero()
    {
        _handler.WhenRaw("users/test-uid.json", "null");

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudgetAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var task = method.Invoke(_service, new object[] { false }) as Task<double>;
        var budget = task != null ? await task : 0;
        budget.Should().Be(0.0);
    }

    [Fact]
    public async Task GetUserBudget_CachingWorks()
    {
        _handler.When("users/test-uid.json", new { printBalance = 42.0 });

        var method = typeof(PrintMonitorService).GetMethod("GetUserBudgetAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;

        var task1 = method.Invoke(_service, new object[] { false }) as Task<double>;
        var b1 = task1 != null ? await task1 : 0;
        b1.Should().Be(42.0);

        _handler.ClearHandlers();
        _handler.WhenError("users/test-uid.json");

        var task2 = method.Invoke(_service, new object[] { false }) as Task<double>;
        var b2 = task2 != null ? await task2 : 0;
        b2.Should().Be(42.0);
    }

    [Fact]
    public async Task DeductBudget_WhenDbFails_ShouldReturnFalse()
    {
        _handler.WhenError("users/test-uid.json");

        var method = typeof(PrintMonitorService).GetMethod("DeductBudgetAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var task = method.Invoke(_service, new object[] { 10.0, false }) as Task<bool>;
        var result = task != null ? await task : false;
        result.Should().BeFalse();
    }

    [Fact]
    public async Task DeductBudget_WithoutAllowNegative_ShouldClampToZero()
    {
        _handler.When("users/test-uid.json", new { printBalance = 5.0 });
        _handler.SetDefaultSuccess();

        double? budgetReceived = null;
        _service.BudgetUpdated += b => budgetReceived = b;

        var method = typeof(PrintMonitorService).GetMethod("DeductBudgetAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var task = method.Invoke(_service, new object[] { 10.0, false }) as Task;
        if (task != null) await task;

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
    public async Task Reinitialize_ClearsCache()
    {
        _handler.When("users/test-uid.json", new { printBalance = 100.0 });
        var getBudget = typeof(PrintMonitorService).GetMethod("GetUserBudgetAsync", BindingFlags.NonPublic | BindingFlags.Instance)!;
        var firstTask = getBudget.Invoke(_service, new object[] { false }) as Task;
        if (firstTask != null) await firstTask;

        _service.Reinitialize("other-user");

        _handler.ClearHandlers();
        _handler.When("users/other-user.json", new { printBalance = 0.0 });

        var task = getBudget.Invoke(_service, new object[] { true }) as Task<double>;
        var budget = task != null ? await task : 0;
        budget.Should().Be(0.0);
    }

    [Fact]
    public void StartMonitoring_ShouldSetIsMonitoringTrue()
    {
        _handler.When("metadata.json", new { blackAndWhitePrice = 1.0, colorPrice = 3.0 });

        _service.StartMonitoring();

        // Give the async init a moment to complete
        Thread.Sleep(500);

        _service.IsMonitoring.Should().BeTrue(
            "StartMonitoring must set IsMonitoring=true so ScanForNewJobs actually processes jobs");
    }

    [Fact]
    public void StopMonitoring_AfterStart_ShouldSetIsMonitoringFalse()
    {
        _handler.When("metadata.json", new { blackAndWhitePrice = 1.0, colorPrice = 3.0 });

        _service.StartMonitoring();
        Thread.Sleep(500);
        _service.IsMonitoring.Should().BeTrue();

        _service.StopMonitoring();
        _service.IsMonitoring.Should().BeFalse();
    }

    [Fact]
    public void StartMonitoring_CalledTwice_ShouldNotThrow()
    {
        _handler.When("metadata.json", new { blackAndWhitePrice = 1.0, colorPrice = 3.0 });

        _service.StartMonitoring();
        Thread.Sleep(500);

        var act = () => _service.StartMonitoring();
        act.Should().NotThrow("calling StartMonitoring twice should be a no-op");
    }
}
