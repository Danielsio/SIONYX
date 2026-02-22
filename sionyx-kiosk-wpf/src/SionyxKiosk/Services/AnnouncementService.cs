using System.Text.Json;
using SionyxKiosk.Infrastructure;
using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

/// <summary>
/// Fetches global admin announcements visible to all users in the organization.
/// These are broadcast messages (new packages, news, promotions) — not user-specific.
/// </summary>
public class AnnouncementService : BaseService
{
    protected override string ServiceName => "AnnouncementService";

    public AnnouncementService(FirebaseClient firebase) : base(firebase) { }

    public async Task<ServiceResult> GetActiveAnnouncementsAsync()
    {
        try
        {
            var (data, error) = await FetchJsonAsync("announcements", "announcements");
            if (error != null)
                return Success(new List<Announcement>());

            if (data.ValueKind != JsonValueKind.Object)
                return Success(new List<Announcement>());

            var announcements = new List<Announcement>();
            var now = DateTime.UtcNow;

            foreach (var prop in data.EnumerateObject())
            {
                if (prop.Value.ValueKind != JsonValueKind.Object) continue;

                var active = true;
                if (prop.Value.TryGetProperty("active", out var activeProp))
                    active = activeProp.ValueKind != JsonValueKind.False;

                if (!active) continue;

                // Check expiry
                if (prop.Value.TryGetProperty("expiresAt", out var expProp) &&
                    expProp.ValueKind == JsonValueKind.String &&
                    DateTime.TryParse(expProp.GetString(), out var expiresAt) &&
                    expiresAt < now)
                    continue;

                announcements.Add(new Announcement
                {
                    Id = prop.Name,
                    Title = SafeGet(prop.Value, "title"),
                    Body = SafeGet(prop.Value, "body"),
                    Type = SafeGet(prop.Value, "type", "info"),
                    CreatedAt = SafeGet(prop.Value, "createdAt"),
                });
            }

            announcements.Sort((a, b) =>
                string.Compare(b.CreatedAt, a.CreatedAt, StringComparison.Ordinal));

            return Success(announcements);
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Failed to load announcements");
            return Success(new List<Announcement>());
        }
    }
}
