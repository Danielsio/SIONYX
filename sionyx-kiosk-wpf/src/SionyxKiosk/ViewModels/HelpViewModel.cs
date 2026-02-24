using System.Collections.ObjectModel;
using System.Windows;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Help page ViewModel: FAQ, admin contact, click-to-copy.</summary>
public partial class HelpViewModel : ObservableObject
{
    private readonly OrganizationMetadataService _orgService;
    private readonly OperatingHoursService _operatingHours;

    [ObservableProperty] private string _adminPhone = "";
    [ObservableProperty] private string _adminEmail = "";
    [ObservableProperty] private string _orgName = "";
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private string _copyFeedback = "";
    [ObservableProperty] private string _workingHoursLine1 = "טוען...";
    [ObservableProperty] private string _workingHoursLine2 = "";

    public ObservableCollection<FaqItem> FaqItems { get; } = new()
    {
        new("איך מתחילים הפעלה?", "לחץ על כפתור 'התחל הפעלה' בדף הבית. ודא שיש לך זמן שימוש זמין."),
        new("איך רוכשים חבילה?", "עבור לעמוד 'חבילות', בחר חבילה ולחץ 'רכוש עכשיו'. התשלום מתבצע באמצעות כרטיס אשראי."),
        new("מה קורה כשנגמר הזמן?", "ההפעלה תסתיים אוטומטית. תקבל התראה 5 דקות ודקה לפני הסיום."),
        new("איך מדפיסים?", "פשוט שלח הדפסה מכל תוכנה. העלות תחויב מיתרת ההדפסות שלך."),
        new("שכחתי סיסמה", "פנה למנהל המערכת בטלפון או באימייל המוצגים למטה."),
    };

    public HelpViewModel(OrganizationMetadataService orgService, OperatingHoursService operatingHours)
    {
        _orgService = orgService;
        _operatingHours = operatingHours;
    }

    [RelayCommand]
    private async Task LoadContactAsync()
    {
        IsLoading = true;
        var result = await _orgService.GetAdminContactAsync();
        IsLoading = false;

        if (result.IsSuccess && result.Data is { } data)
        {
            var type = data.GetType();
            AdminPhone = type.GetProperty("phone")?.GetValue(data)?.ToString() ?? "";
            AdminEmail = type.GetProperty("email")?.GetValue(data)?.ToString() ?? "";
            OrgName = type.GetProperty("orgName")?.GetValue(data)?.ToString() ?? "";
        }

        await _operatingHours.LoadSettingsAsync();
        var s = _operatingHours.Settings;
        if (s.Enabled)
        {
            WorkingHoursLine1 = $"{s.StartTime} - {s.EndTime}";
            WorkingHoursLine2 = "";
        }
        else
        {
            WorkingHoursLine1 = "24/7";
            WorkingHoursLine2 = "ללא הגבלת שעות";
        }
    }

    [RelayCommand]
    private async Task CopyToClipboardAsync(string text)
    {
        if (string.IsNullOrWhiteSpace(text)) return;

        try
        {
            Clipboard.SetText(text);
            CopyFeedback = "הועתק!";

            await Task.Delay(2000);
            CopyFeedback = "";
        }
        catch
        {
            CopyFeedback = "שגיאה בהעתקה";
        }
    }
}

public record FaqItem(string Question, string Answer);
