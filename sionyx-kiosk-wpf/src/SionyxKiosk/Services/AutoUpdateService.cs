using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;
using Serilog;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Kiosk auto-update. Reads release metadata from RTDB <c>public/latestRelease</c>
/// (written by the release workflow), downloads the installer from GitHub Releases,
/// verifies its SHA-256, and installs it. No always-on update server (the fork
/// polled a Render endpoint); the metadata lives in the free Realtime Database.
/// </summary>
public static class AutoUpdateService
{
    private static readonly ILogger Logger = Log.ForContext(typeof(AutoUpdateService));
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromMinutes(10) };

    public sealed record ReleaseInfo(string Version, string DownloadUrl, string? Sha256);

    /// <summary>Check for a newer release and install it if found. Best-effort; never throws.</summary>
    public static async Task CheckAndUpdateAsync()
    {
        try
        {
            string dbUrl;
            try { dbUrl = FirebaseConfig.Load().DatabaseUrl; }
            catch (Exception ex) { Logger.Warning(ex, "[Update] no config; skipping"); return; }

            var current = GetCurrentVersion();
            var latest = await FetchLatestAsync(dbUrl);
            if (latest is null) { Logger.Information("[Update] no release metadata"); return; }

            if (!IsNewerVersion(latest.Version, current))
            {
                Logger.Information("[Update] up to date ({Current})", current);
                return;
            }

            Logger.Information("[Update] new version available: {Latest} (current {Current})", latest.Version, current);
            var msi = await DownloadAndVerifyAsync(latest);
            if (msi is null) return;
            StageUpdate(msi, latest.Sha256);
        }
        catch (Exception ex)
        {
            Logger.Warning(ex, "[Update] check failed (non-fatal)");
        }
    }

    /// <summary>Running app version, read from the bundled version.json.</summary>
    public static string GetCurrentVersion()
    {
        try
        {
            var path = Path.Combine(AppContext.BaseDirectory, "version.json");
            if (File.Exists(path))
            {
                using var doc = JsonDocument.Parse(File.ReadAllText(path));
                if (doc.RootElement.TryGetProperty("version", out var v) && v.ValueKind == JsonValueKind.String)
                    return v.GetString() ?? "1.0.0";
            }
        }
        catch { /* fall back */ }
        return "1.0.0";
    }

    /// <summary>Fetch release metadata from RTDB public/latestRelease (public read, no auth).</summary>
    public static async Task<ReleaseInfo?> FetchLatestAsync(string databaseUrl)
    {
        var url = $"{databaseUrl.TrimEnd('/')}/public/latestRelease.json?t={DateTime.UtcNow.Ticks}";
        using var resp = await Http.GetAsync(url);
        if (!resp.IsSuccessStatusCode) return null;
        using var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
        if (doc.RootElement.ValueKind != JsonValueKind.Object) return null;
        var root = doc.RootElement;
        var version = root.TryGetProperty("version", out var v) ? v.GetString() : null;
        var dl = root.TryGetProperty("downloadUrl", out var d) ? d.GetString() : null;
        var sha = root.TryGetProperty("sha256", out var s) && s.ValueKind == JsonValueKind.String ? s.GetString() : null;
        if (string.IsNullOrEmpty(version) || string.IsNullOrEmpty(dl)) return null;
        return new ReleaseInfo(version!, dl!, sha);
    }

    /// <summary>True if <paramref name="latest"/> is a strictly newer version than <paramref name="current"/>.</summary>
    public static bool IsNewerVersion(string latest, string current)
    {
        try { return Version.Parse(latest.TrimStart('v')) > Version.Parse(current.TrimStart('v')); }
        catch { return string.CompareOrdinal(latest, current) > 0; }
    }

    /// <summary>Lowercase hex SHA-256 of a file.</summary>
    public static string ComputeSha256(string filePath)
    {
        using var sha = SHA256.Create();
        using var stream = File.OpenRead(filePath);
        return Convert.ToHexString(sha.ComputeHash(stream)).ToLowerInvariant();
    }

    private static async Task<string?> DownloadAndVerifyAsync(ReleaseInfo info)
    {
        var folder = Path.Combine(Path.GetTempPath(), "sionyx_update");
        Directory.CreateDirectory(folder);
        var dest = Path.Combine(folder, $"sionyx_{info.Version}_{DateTime.UtcNow.Ticks}.msi");

        Logger.Information("[Update] downloading {Url}", info.DownloadUrl);
        using (var resp = await Http.GetAsync(info.DownloadUrl, HttpCompletionOption.ResponseHeadersRead))
        {
            resp.EnsureSuccessStatusCode();
            await using var fs = File.Create(dest);
            await resp.Content.CopyToAsync(fs);
        }

        if (!string.IsNullOrEmpty(info.Sha256))
        {
            var actual = ComputeSha256(dest);
            if (!string.Equals(actual, info.Sha256, StringComparison.OrdinalIgnoreCase))
            {
                Logger.Error("[Update] SHA-256 mismatch (expected {Exp}, got {Got}) — discarding", info.Sha256, actual);
                try { File.Delete(dest); } catch { /* ignore */ }
                return null;
            }
            Logger.Information("[Update] SHA-256 verified");
        }
        else
        {
            Logger.Warning("[Update] no SHA-256 in metadata — installing unverified");
        }
        return dest;
    }

    private static void StageUpdate(string msiPath, string? sha256)
    {
        // Preferred path: hand the verified MSI to the SYSTEM "SIONYX Update" scheduled
        // task (registered by the installer), which installs it silently with NO UAC
        // prompt — the kiosk runs as a non-admin user and cannot elevate interactively.
        // Falls back to a direct (elevating) msiexec if staging isn't possible.
        try
        {
            var updateDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "SIONYX", "update");
            Directory.CreateDirectory(updateDir);
            var pending = Path.Combine(updateDir, "pending.json");
            File.WriteAllText(pending, JsonSerializer.Serialize(new { MsiPath = msiPath, Sha256 = sha256 ?? "" }));
            Logger.Information("[Update] staged update request at {Path}", pending);

            // Best-effort immediate kick; otherwise the task's own schedule (boot +
            // every 15 min) applies it. A non-admin user may not be able to /run it —
            // that's fine, the scheduled trigger is the guarantee.
            try
            {
                Process.Start(new ProcessStartInfo("schtasks.exe", "/run /tn \"SIONYX Update\"")
                {
                    UseShellExecute = false,
                    CreateNoWindow = true,
                });
            }
            catch (Exception ex)
            {
                Logger.Warning(ex, "[Update] could not trigger update task now; it will run on schedule");
            }
            return;
        }
        catch (Exception ex)
        {
            Logger.Warning(ex, "[Update] staging failed; falling back to direct install");
        }

        try
        {
            Logger.Information("[Update] launching installer directly {Path}", msiPath);
            Process.Start(new ProcessStartInfo("msiexec.exe", $"/i \"{msiPath}\" /qn /norestart")
            {
                UseShellExecute = true,
            });
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "[Update] direct install launch failed");
        }
    }
}
