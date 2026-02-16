using System.Text.Json;
using FluentAssertions;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Services;

namespace SionyxKiosk.Tests.Services;

/// <summary>Concrete subclass to test BaseService abstract members.</summary>
public class TestableService : BaseService
{
    protected override string ServiceName => "TestService";

    public TestableService(FirebaseClient firebase) : base(firebase) { }

    // Expose protected methods for testing
    public ServiceResult CallSuccess(object? data = null, string? message = null) => Success(data, message);
    public ServiceResult CallError(string error, string? code = null) => Error(error, code);
    public bool CallIsAuthenticated() => IsAuthenticated();
    public ServiceResult CallRequireAuthentication() => RequireAuthentication();
    public string CallSafeGet(JsonElement el, string prop, string def = "") => SafeGet(el, prop, def);
    public int CallSafeGetInt(JsonElement el, string prop, int def = 0) => SafeGetInt(el, prop, def);
    public double CallSafeGetDouble(JsonElement el, string prop, double def = 0.0) => SafeGetDouble(el, prop, def);
    public string CallHandleFirebaseError(Exception ex, string op) => HandleFirebaseError(ex, op);
    public void CallLogOperation(string op, string? details = null) => LogOperation(op, details);
}

public class BaseServiceTests : IDisposable
{
    private readonly FirebaseClient _client;
    private readonly TestableService _service;

    public BaseServiceTests()
    {
        (_client, _) = TestFirebaseFactory.Create();
        _service = new TestableService(_client);
    }

    public void Dispose() => _client.Dispose();

    // ==================== RESPONSE HELPERS ====================

    [Fact]
    public void Success_WithoutArgs_ShouldReturnSuccess()
    {
        var result = _service.CallSuccess();
        result.IsSuccess.Should().BeTrue();
        result.Data.Should().BeNull();
        result.Message.Should().BeNull();
        result.Error.Should().BeNull();
    }

    [Fact]
    public void Success_WithData_ShouldReturnData()
    {
        var data = new { name = "Test" };
        var result = _service.CallSuccess(data, "OK");
        result.IsSuccess.Should().BeTrue();
        result.Data.Should().Be(data);
        result.Message.Should().Be("OK");
    }

    [Fact]
    public void Error_ShouldReturnError()
    {
        var result = _service.CallError("Something failed", "ERR_CODE");
        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Be("Something failed");
        result.ErrorCode.Should().Be("ERR_CODE");
    }

    // ==================== AUTH CHECKS ====================

    [Fact]
    public void IsAuthenticated_WhenTokenSet_ShouldReturnTrue()
    {
        _service.CallIsAuthenticated().Should().BeTrue();
    }

    [Fact]
    public void IsAuthenticated_WhenCleared_ShouldReturnFalse()
    {
        _client.ClearAuth();
        _service.CallIsAuthenticated().Should().BeFalse();
    }

    [Fact]
    public void RequireAuthentication_WhenAuthenticated_ShouldReturnSuccess()
    {
        var result = _service.CallRequireAuthentication();
        result.IsSuccess.Should().BeTrue();
    }

    [Fact]
    public void RequireAuthentication_WhenNotAuthenticated_ShouldReturnError()
    {
        _client.ClearAuth();
        var result = _service.CallRequireAuthentication();
        result.IsSuccess.Should().BeFalse();
        result.ErrorCode.Should().Be("AUTH_REQUIRED");
    }

    // ==================== SAFE HELPERS ====================

    [Fact]
    public void SafeGet_WithExistingProperty_ShouldReturnValue()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { name = "John" });
        _service.CallSafeGet(el, "name").Should().Be("John");
    }

    [Fact]
    public void SafeGet_WithMissingProperty_ShouldReturnDefault()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { name = "John" });
        _service.CallSafeGet(el, "missing", "default").Should().Be("default");
    }

    [Fact]
    public void SafeGet_WithNullElement_ShouldReturnDefault()
    {
        var el = TestFirebaseFactory.ToJsonElement((object?)null!);
        _service.CallSafeGet(el, "any", "fallback").Should().Be("fallback");
    }

    [Fact]
    public void SafeGetInt_WithNumber_ShouldReturnValue()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { count = 42 });
        _service.CallSafeGetInt(el, "count").Should().Be(42);
    }

    [Fact]
    public void SafeGetInt_WithStringNumber_ShouldParse()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { count = "99" });
        _service.CallSafeGetInt(el, "count").Should().Be(99);
    }

    [Fact]
    public void SafeGetInt_WithMissing_ShouldReturnDefault()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { name = "John" });
        _service.CallSafeGetInt(el, "count", 10).Should().Be(10);
    }

    [Fact]
    public void SafeGetDouble_WithNumber_ShouldReturnValue()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { price = 9.99 });
        _service.CallSafeGetDouble(el, "price").Should().Be(9.99);
    }

    [Fact]
    public void SafeGetDouble_WithStringNumber_ShouldParse()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { price = "19.50" });
        _service.CallSafeGetDouble(el, "price").Should().Be(19.50);
    }

    [Fact]
    public void SafeGetDouble_WithMissing_ShouldReturnDefault()
    {
        var el = TestFirebaseFactory.ToJsonElement(new { name = "John" });
        _service.CallSafeGetDouble(el, "price", 5.0).Should().Be(5.0);
    }

    // ==================== ERROR HANDLING ====================

    [Fact]
    public void HandleFirebaseError_ShouldTranslateError()
    {
        var ex = new Exception("network error");
        var result = _service.CallHandleFirebaseError(ex, "TestOp");
        result.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public void LogOperation_ShouldNotThrow()
    {
        var act = () => _service.CallLogOperation("TestOp", "some details");
        act.Should().NotThrow();
    }

    [Fact]
    public void LogOperation_WithoutDetails_ShouldNotThrow()
    {
        var act = () => _service.CallLogOperation("TestOp");
        act.Should().NotThrow();
    }
}

public class ServiceResultTests
{
    [Fact]
    public void GetData_WithCorrectType_ShouldReturn()
    {
        var data = new List<string> { "a", "b" };
        var result = new ServiceResult { IsSuccess = true, Data = data };
        result.GetData<List<string>>().Should().BeSameAs(data);
    }

    [Fact]
    public void GetData_WithWrongType_ShouldReturnNull()
    {
        var result = new ServiceResult { IsSuccess = true, Data = "string" };
        result.GetData<List<string>>().Should().BeNull();
    }

    [Fact]
    public void GetData_WithNull_ShouldReturnNull()
    {
        var result = new ServiceResult { IsSuccess = true, Data = null };
        result.GetData<object>().Should().BeNull();
    }

    [Fact]
    public void Properties_ShouldBeSettable()
    {
        var result = new ServiceResult
        {
            IsSuccess = false,
            Error = "test error",
            ErrorCode = "ERR",
            Message = "msg",
            Data = 42,
        };

        result.IsSuccess.Should().BeFalse();
        result.Error.Should().Be("test error");
        result.ErrorCode.Should().Be("ERR");
        result.Message.Should().Be("msg");
        result.Data.Should().Be(42);
    }
}
