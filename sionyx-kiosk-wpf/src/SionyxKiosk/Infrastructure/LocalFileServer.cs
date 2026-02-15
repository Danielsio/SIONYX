using System.IO;
using System.Net;
using System.Text;
using Serilog;

namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Simple local HTTP file server for serving payment HTML pages.
/// Uses built-in .NET HttpListener (no external dependencies).
/// </summary>
public class LocalFileServer : IDisposable
{
    private static readonly ILogger Log = Serilog.Log.ForContext<LocalFileServer>();
    private HttpListener? _listener;
    private readonly string _rootDir;
    private readonly int _port;
    private CancellationTokenSource? _cts;
    private Task? _serverTask;

    public string BaseUrl => $"http://localhost:{_port}/";

    public LocalFileServer(string rootDir, int port = 8765)
    {
        _rootDir = rootDir;
        _port = port;
    }

    public void Start()
    {
        if (_listener != null) return;

        _listener = new HttpListener();
        _listener.Prefixes.Add(BaseUrl);
        _listener.Start();
        _cts = new CancellationTokenSource();

        _serverTask = Task.Run(() => ListenLoop(_cts.Token));
        Log.Information("LocalFileServer: started on {Url}, root={Root}", BaseUrl, _rootDir);
    }

    public void Stop()
    {
        _cts?.Cancel();
        _listener?.Stop();
        _listener?.Close();
        _listener = null;
        _cts = null;
        Log.Information("LocalFileServer: stopped");
    }

    private async Task ListenLoop(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested && _listener != null)
        {
            try
            {
                var context = await _listener.GetContextAsync();
                _ = Task.Run(() => HandleRequest(context), ct);
            }
            catch (HttpListenerException) when (ct.IsCancellationRequested)
            {
                break;
            }
            catch (ObjectDisposedException)
            {
                break;
            }
            catch (Exception ex)
            {
                Log.Error(ex, "LocalFileServer: error accepting connection");
            }
        }
    }

    private void HandleRequest(HttpListenerContext context)
    {
        var request = context.Request;
        var response = context.Response;

        try
        {
            var path = request.Url?.LocalPath?.TrimStart('/') ?? "index.html";
            if (string.IsNullOrEmpty(path)) path = "index.html";

            var filePath = Path.Combine(_rootDir, path);

            // Prevent directory traversal
            var fullRoot = Path.GetFullPath(_rootDir);
            var fullFile = Path.GetFullPath(filePath);
            if (!fullFile.StartsWith(fullRoot, StringComparison.OrdinalIgnoreCase))
            {
                response.StatusCode = 403;
                response.Close();
                return;
            }

            if (File.Exists(filePath))
            {
                var content = File.ReadAllBytes(filePath);
                response.ContentType = GetContentType(filePath);
                response.ContentLength64 = content.Length;
                response.StatusCode = 200;

                // CORS headers for local dev
                response.Headers.Add("Access-Control-Allow-Origin", "*");

                response.OutputStream.Write(content, 0, content.Length);
            }
            else
            {
                response.StatusCode = 404;
                var msg = Encoding.UTF8.GetBytes("Not Found");
                response.OutputStream.Write(msg, 0, msg.Length);
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "LocalFileServer: error handling request");
            response.StatusCode = 500;
        }
        finally
        {
            response.Close();
        }
    }

    private static string GetContentType(string path)
    {
        return Path.GetExtension(path).ToLowerInvariant() switch
        {
            ".html" or ".htm" => "text/html; charset=utf-8",
            ".css" => "text/css; charset=utf-8",
            ".js" => "application/javascript; charset=utf-8",
            ".json" => "application/json; charset=utf-8",
            ".png" => "image/png",
            ".jpg" or ".jpeg" => "image/jpeg",
            ".svg" => "image/svg+xml",
            ".ico" => "image/x-icon",
            _ => "application/octet-stream"
        };
    }

    public void Dispose()
    {
        Stop();
        GC.SuppressFinalize(this);
    }
}
