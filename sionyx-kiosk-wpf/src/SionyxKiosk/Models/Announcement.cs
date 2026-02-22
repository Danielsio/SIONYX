namespace SionyxKiosk.Models;

/// <summary>
/// Global admin announcement visible to all users in the organization.
/// Stored at organizations/{orgId}/announcements/{id} in Firebase RTDB.
/// </summary>
public class Announcement
{
    public string Id { get; set; } = "";
    public string Title { get; set; } = "";
    public string Body { get; set; } = "";
    /// <summary>info | success | warning | promotion</summary>
    public string Type { get; set; } = "info";
    public string CreatedAt { get; set; } = "";

    public string Icon => Type switch
    {
        "success" => "✅",
        "warning" => "⚠",
        "promotion" => "🎁",
        _ => "📢",
    };

    public string AccentColor => Type switch
    {
        "success" => "#10B981",
        "warning" => "#F59E0B",
        "promotion" => "#8B5CF6",
        _ => "#3B82F6",
    };

    public string BackgroundColor => Type switch
    {
        "success" => "#F0FDF4",
        "warning" => "#FFFBEB",
        "promotion" => "#F5F3FF",
        _ => "#EFF6FF",
    };

    public string BorderColor => Type switch
    {
        "success" => "#BBF7D0",
        "warning" => "#FDE68A",
        "promotion" => "#DDD6FE",
        _ => "#BFDBFE",
    };
}
