using System.IO;
using System.Net.Http;
using FluentAssertions;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Tests.Infrastructure;

public class LocalFileServerTests : IDisposable
{
    private readonly string _tempDir;
    private readonly LocalFileServer _server;

    public LocalFileServerTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), $"sionyx_test_{Guid.NewGuid():N}");
        Directory.CreateDirectory(_tempDir);
        _server = new LocalFileServer(_tempDir, 0); // port 0 won't work; use a fixed port
    }

    [Fact]
    public void Constructor_ShouldSetBaseUrl()
    {
        var server = new LocalFileServer(_tempDir, 9876);
        server.BaseUrl.Should().Be("http://localhost:9876/");
    }

    [Fact]
    public void StartStop_ShouldNotThrow()
    {
        var server = new LocalFileServer(_tempDir, 19876);
        var startAct = () => server.Start();
        startAct.Should().NotThrow();

        var stopAct = () => server.Stop();
        stopAct.Should().NotThrow();
    }

    [Fact]
    public async Task Serve_ShouldReturnFileContent()
    {
        // Create a test file
        File.WriteAllText(Path.Combine(_tempDir, "test.html"), "<html>Hello</html>");

        var server = new LocalFileServer(_tempDir, 19877);
        server.Start();

        try
        {
            using var client = new HttpClient();
            var response = await client.GetStringAsync("http://localhost:19877/test.html");
            response.Should().Contain("Hello");
        }
        finally
        {
            server.Stop();
        }
    }

    [Fact]
    public async Task Serve_MissingFile_ShouldReturn404()
    {
        var server = new LocalFileServer(_tempDir, 19878);
        server.Start();

        try
        {
            using var client = new HttpClient();
            var response = await client.GetAsync("http://localhost:19878/nonexistent.html");
            response.StatusCode.Should().Be(System.Net.HttpStatusCode.NotFound);
        }
        finally
        {
            server.Stop();
        }
    }

    public void Dispose()
    {
        _server.Dispose();
        if (Directory.Exists(_tempDir))
            Directory.Delete(_tempDir, recursive: true);
    }
}
