using System.IO;
using System.Net.Http;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

/// <summary>
/// Tests for LocalFileServer covering Start, Stop, serving files, and error handling.
/// </summary>
public class LocalFileServerTests : IDisposable
{
    private readonly string _tempDir;
    private LocalFileServer? _server;

    public LocalFileServerTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), $"lfs_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(_tempDir);
    }

    public void Dispose()
    {
        _server?.Dispose();
        try { Directory.Delete(_tempDir, true); } catch { }
    }

    [Fact]
    public void Constructor_WithSpecificPort_ShouldSetBaseUrl()
    {
        _server = new LocalFileServer(_tempDir, 0); // 0 = find free port
        _server.BaseUrl.Should().StartWith("http://localhost:");
    }

    [Fact]
    public void Constructor_WithDefaultPort_ShouldSetBaseUrl()
    {
        _server = new LocalFileServer(_tempDir, 8999);
        _server.BaseUrl.Should().Be("http://localhost:8999/");
    }

    [Fact]
    public void Start_ShouldNotThrow()
    {
        _server = new LocalFileServer(_tempDir, 0);
        var act = () => _server.Start();
        act.Should().NotThrow();
        _server.Stop();
    }

    [Fact]
    public void Start_MultipleTimes_ShouldBeIdempotent()
    {
        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();
        var act = () => _server.Start(); // Should be no-op
        act.Should().NotThrow();
        _server.Stop();
    }

    [Fact]
    public void Stop_WhenNotStarted_ShouldNotThrow()
    {
        _server = new LocalFileServer(_tempDir, 0);
        var act = () => _server.Stop();
        act.Should().NotThrow();
    }

    [Fact]
    public void Dispose_ShouldStopServer()
    {
        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();
        _server.Dispose();
        _server = null; // Prevent double dispose
    }

    [Fact]
    public async Task Server_ShouldServeHtmlFile()
    {
        // Create test file
        File.WriteAllText(Path.Combine(_tempDir, "index.html"), "<html><body>Test</body></html>");

        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl + "index.html");
        response.StatusCode.Should().Be(System.Net.HttpStatusCode.OK);

        var content = await response.Content.ReadAsStringAsync();
        content.Should().Contain("Test");
    }

    [Fact]
    public async Task Server_ShouldReturn404ForMissingFile()
    {
        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl + "missing.html");
        response.StatusCode.Should().Be(System.Net.HttpStatusCode.NotFound);
    }

    [Fact]
    public async Task Server_ShouldPreventDirectoryTraversal()
    {
        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl + "../../../etc/passwd");
        response.StatusCode.Should().BeOneOf(
            System.Net.HttpStatusCode.Forbidden,
            System.Net.HttpStatusCode.NotFound,
            System.Net.HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task Server_ShouldServeJsonWithCorrectContentType()
    {
        File.WriteAllText(Path.Combine(_tempDir, "data.json"), "{\"test\": true}");

        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl + "data.json");
        response.StatusCode.Should().Be(System.Net.HttpStatusCode.OK);
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/json");
    }

    [Fact]
    public async Task Server_ShouldServeCssWithCorrectContentType()
    {
        File.WriteAllText(Path.Combine(_tempDir, "style.css"), "body { color: red; }");

        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl + "style.css");
        response.StatusCode.Should().Be(System.Net.HttpStatusCode.OK);
        response.Content.Headers.ContentType?.MediaType.Should().Be("text/css");
    }

    [Fact]
    public async Task Server_ShouldServeJsWithCorrectContentType()
    {
        File.WriteAllText(Path.Combine(_tempDir, "app.js"), "console.log('hello');");

        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl + "app.js");
        response.StatusCode.Should().Be(System.Net.HttpStatusCode.OK);
        response.Content.Headers.ContentType?.MediaType.Should().Be("application/javascript");
    }

    [Fact]
    public async Task Server_ShouldIncludeCorsHeaders()
    {
        File.WriteAllText(Path.Combine(_tempDir, "test.html"), "<html></html>");

        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl + "test.html");
        response.Headers.TryGetValues("Access-Control-Allow-Origin", out var values);
        values.Should().Contain("*");
    }

    [Fact]
    public async Task Server_RootPath_ShouldServeIndexHtml()
    {
        File.WriteAllText(Path.Combine(_tempDir, "index.html"), "<html>Root</html>");

        _server = new LocalFileServer(_tempDir, 0);
        _server.Start();

        using var client = new HttpClient();
        var response = await client.GetAsync(_server.BaseUrl);
        var content = await response.Content.ReadAsStringAsync();
        content.Should().Contain("Root");
    }
}
