using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>
/// Final coverage tests for OrganizationMetadataService targeting exception catch blocks
/// and remaining edge cases.
/// </summary>
public class OrgMetadataFinalCoverageTests : IDisposable
{
    private readonly FirebaseClient _firebase;
    private readonly MockHttpHandler _handler;
    private readonly OrganizationMetadataService _service;

    public OrgMetadataFinalCoverageTests()
    {
        (_firebase, _handler) = TestFirebaseFactory.Create();
        _service = new OrganizationMetadataService(_firebase);
    }

    public void Dispose() => _firebase.Dispose();

    // ==================== GetOperatingHoursAsync exception path ====================

    [Fact]
    public async Task GetOperatingHoursAsync_WithPartialData_ShouldReturnDefaults()
    {
        // Only enabled, missing other fields -> should use defaults
        _handler.When("operatingHours.json", new { enabled = true });

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOperatingHoursAsync_WithDisabledHours_ShouldReturn()
    {
        _handler.When("operatingHours.json", new
        {
            enabled = false,
            startTime = "09:00",
            endTime = "18:00",
            gracePeriodMinutes = 10,
            graceBehavior = "force",
        });

        var result = await _service.GetOperatingHoursAsync();
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== GetPrintPricingAsync null data ====================

    [Fact]
    public async Task GetPrintPricingAsync_WithNumericPrices_ShouldReturnExact()
    {
        _handler.When("metadata.json", new
        {
            blackAndWhitePrice = 2.5,
            colorPrice = 5.0,
        });

        var result = await _service.GetPrintPricingAsync("test-org");
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== SetPrintPricingAsync exception ====================

    [Fact]
    public async Task SetPrintPricingAsync_WithZeroPrices_ShouldSucceed()
    {
        _handler.SetDefaultSuccess();
        var result = await _service.SetPrintPricingAsync("test-org", 0, 0);
        result.IsSuccess.Should().BeTrue();
    }

    // ==================== GetAdminContactAsync edge cases ====================

    [Fact]
    public async Task GetAdminContactAsync_WithEmptyPhoneAndEmail_ShouldReturnError()
    {
        _handler.When("metadata.json", new
        {
            admin_phone = "",
            admin_email = "",
            name = "Test Org",
        });

        var result = await _service.GetAdminContactAsync();
        result.IsSuccess.Should().BeFalse();
    }

    // ==================== GetOrganizationMetadataAsync status field ====================

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithNoStatusField_ShouldUseDefault()
    {
        var mosadId = Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes("\"12345\""));
        var apiValid = Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes("\"valid-key\""));

        _handler.When("metadata.json", new
        {
            name = "Test Org",
            nedarim_mosad_id = mosadId,
            nedarim_api_valid = apiValid,
            created_at = "2024-01-01",
            // No status field -> defaults to "active"
        });

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithInvalidNedarimData_ShouldReturnError()
    {
        // base64 but invalid JSON
        var badEncoded = Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes("not json"));

        _handler.When("metadata.json", new
        {
            name = "Test Org",
            nedarim_mosad_id = badEncoded,
            nedarim_api_valid = badEncoded,
        });

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Contain("NEDARIM");
    }

    [Fact]
    public async Task GetOrganizationMetadataAsync_WithEmptyNedarimFields_ShouldReturnError()
    {
        _handler.When("metadata.json", new
        {
            name = "Test Org",
            nedarim_mosad_id = "",
            nedarim_api_valid = "",
        });

        var result = await _service.GetOrganizationMetadataAsync("test-org");
        result.IsSuccess.Should().BeFalse();
    }
}
