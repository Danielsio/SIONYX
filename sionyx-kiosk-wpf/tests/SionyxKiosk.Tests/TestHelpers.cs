using System.Net;
using System.Reflection;
using System.Text;
using System.Text.Json;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests;

/// <summary>
/// Mock HTTP handler that returns controlled responses for Firebase API calls.
/// </summary>
public class MockHttpHandler : HttpMessageHandler
{
    private readonly List<(string Pattern, Func<HttpRequestMessage, HttpResponseMessage> Factory)> _handlers = new();
    private Func<HttpRequestMessage, HttpResponseMessage> _defaultFactory;

    public List<HttpRequestMessage> SentRequests { get; } = new();

    public MockHttpHandler()
    {
        _defaultFactory = _ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("null", Encoding.UTF8, "application/json")
        };
    }

    /// <summary>When URL contains pattern, return this JSON.</summary>
    public void When(string urlContains, object jsonData)
    {
        var json = JsonSerializer.Serialize(jsonData);
        _handlers.Add((urlContains, _ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json")
        }));
    }

    /// <summary>When URL contains pattern, return this raw JSON string.</summary>
    public void WhenRaw(string urlContains, string rawJson)
    {
        _handlers.Add((urlContains, _ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(rawJson, Encoding.UTF8, "application/json")
        }));
    }

    /// <summary>When URL contains pattern, return error.</summary>
    public void WhenError(string urlContains, HttpStatusCode statusCode = HttpStatusCode.InternalServerError)
    {
        _handlers.Add((urlContains, _ => new HttpResponseMessage(statusCode)
        {
            Content = new StringContent("{\"error\":\"test error\"}", Encoding.UTF8, "application/json")
        }));
    }

    /// <summary>When URL contains pattern, return a Firebase auth-style error (400).</summary>
    public void WhenFirebaseError(string urlContains, string errorCode)
    {
        var body = JsonSerializer.Serialize(new { error = new { message = errorCode } });
        _handlers.Add((urlContains, _ => new HttpResponseMessage(HttpStatusCode.BadRequest)
        {
            Content = new StringContent(body, Encoding.UTF8, "application/json")
        }));
    }

    /// <summary>Clear all registered handlers.</summary>
    public void ClearHandlers()
    {
        _handlers.Clear();
    }

    /// <summary>When URL contains pattern, throw an exception (simulates network failure).</summary>
    public void WhenThrows(string urlContains, string message = "Network error")
    {
        _handlers.Add((urlContains, _ => throw new HttpRequestException(message)));
    }

    /// <summary>Set default response for all unmatched URLs.</summary>
    public void SetDefault(object jsonData)
    {
        var json = JsonSerializer.Serialize(jsonData);
        _defaultFactory = _ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json")
        };
    }

    /// <summary>Set default to success (empty JSON object).</summary>
    public void SetDefaultSuccess()
    {
        _defaultFactory = _ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent("{}", Encoding.UTF8, "application/json")
        };
    }

    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken ct)
    {
        SentRequests.Add(request);

        var url = request.RequestUri?.ToString() ?? "";
        foreach (var (pattern, factory) in _handlers)
        {
            if (url.Contains(pattern, StringComparison.OrdinalIgnoreCase))
                return Task.FromResult(factory(request));
        }

        return Task.FromResult(_defaultFactory(request));
    }
}

/// <summary>
/// Factory for creating FirebaseClient instances in tests.
/// Uses reflection to construct FirebaseConfig (private constructor).
/// </summary>
public static class TestFirebaseFactory
{
    /// <summary>Create an authenticated FirebaseClient with a mock HTTP handler.</summary>
    public static (FirebaseClient Client, MockHttpHandler Handler) Create(string userId = "test-uid")
    {
        var handler = new MockHttpHandler();
        handler.SetDefaultSuccess();
        var httpClient = new HttpClient(handler);

        var config = CreateConfig();
        var client = new FirebaseClient(config, httpClient);
        client.RestoreAuth("test-id-token", "test-refresh-token", userId);

        return (client, handler);
    }

    /// <summary>Create an unauthenticated FirebaseClient with a mock HTTP handler.</summary>
    public static (FirebaseClient Client, MockHttpHandler Handler) CreateUnauthenticated()
    {
        var handler = new MockHttpHandler();
        handler.SetDefaultSuccess();
        var httpClient = new HttpClient(handler);

        var config = CreateConfig();
        var client = new FirebaseClient(config, httpClient);

        return (client, handler);
    }

    /// <summary>Create a FirebaseConfig via reflection (private constructor).</summary>
    public static FirebaseConfig CreateConfig(
        string apiKey = "test-api-key",
        string? authDomain = "test.firebaseapp.com",
        string databaseUrl = "https://test-db.firebaseio.com",
        string projectId = "test-project",
        string orgId = "test-org")
    {
        var ctor = typeof(FirebaseConfig).GetConstructor(
            BindingFlags.NonPublic | BindingFlags.Instance,
            null,
            new[] { typeof(string), typeof(string), typeof(string), typeof(string), typeof(string) },
            null);

        return (FirebaseConfig)ctor!.Invoke(new object?[] { apiKey, authDomain, databaseUrl, projectId, orgId });
    }

    /// <summary>Create a JsonElement from an anonymous object.</summary>
    public static JsonElement ToJsonElement(object obj)
    {
        var json = JsonSerializer.Serialize(obj);
        return JsonSerializer.Deserialize<JsonElement>(json);
    }
}
