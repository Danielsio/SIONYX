namespace SionyxKiosk.Models;

/// <summary>
/// User data model matching the Firebase RTDB structure.
/// </summary>
public class UserData
{
    public string Uid { get; set; } = "";
    public string FirstName { get; set; } = "";
    public string LastName { get; set; } = "";
    public string PhoneNumber { get; set; } = "";
    public string Email { get; set; } = "";
    public int RemainingTime { get; set; }
    public double PrintBalance { get; set; }
    public bool IsLoggedIn { get; set; }
    public bool IsBlocked { get; set; }
    public bool IsAdmin { get; set; }

    /// <summary>
    /// An admin approved this user's phone in the web console. Only enforced when
    /// the org turns on requirePhoneVerification.
    /// </summary>
    public bool PhoneVerified { get; set; }

    public bool IsSessionActive { get; set; }
    public string? SessionStartTime { get; set; }
    public string? CurrentComputerId { get; set; }
    public string? TimeExpiresAt { get; set; }
    public string? LastSeen { get; set; }
    public string CreatedAt { get; set; } = "";
    public string UpdatedAt { get; set; } = "";

    public string FullName => $"{FirstName} {LastName}".Trim();
}
