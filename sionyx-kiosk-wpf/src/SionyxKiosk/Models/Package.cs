namespace SionyxKiosk.Models;

/// <summary>
/// Package model matching the Firebase RTDB structure.
/// </summary>
public class Package
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public double Price { get; set; }
    public int Minutes { get; set; }
    public int Prints { get; set; }
    public double DiscountPercent { get; set; }
    public int ValidityDays { get; set; }
    public bool IsFeatured { get; set; }

    public double FinalPrice => Math.Round(Price * (1 - DiscountPercent / 100), 2);
    public double Savings => Math.Round(Price - FinalPrice, 2);
}

/// <summary>
/// Purchase record matching the Firebase RTDB structure.
/// </summary>
public class Purchase
{
    public string Id { get; set; } = "";
    public string UserId { get; set; } = "";
    public string PackageId { get; set; } = "";
    public string PackageName { get; set; } = "";
    public int Minutes { get; set; }
    public int Prints { get; set; }
    public double PrintBudget { get; set; }
    public int ValidityDays { get; set; }
    public double Amount { get; set; }
    public string Status { get; set; } = "pending";
    public string CreatedAt { get; set; } = "";
    public string UpdatedAt { get; set; } = "";
}
