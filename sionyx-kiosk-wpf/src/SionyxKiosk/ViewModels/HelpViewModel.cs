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
    [ObservableProperty] private string _workingHoursLine3 = "";

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
        if (s.Enabled && s.Schedule.Count > 0)
        {
            var dayLabels = new[] { "א'", "ב'", "ג'", "ד'", "ה'", "ו'", "שבת" };
            var dayKeys = new[] { "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday" };
            var lines = new List<string>();
            for (int i = 0; i < dayKeys.Length; i++)
            {
                if (s.Schedule.TryGetValue(dayKeys[i], out var ds))
                    lines.Add(ds.Open ? $"{dayLabels[i]} {ds.StartTime}-{ds.EndTime}" : $"{dayLabels[i]} סגור");
                else
                    lines.Add($"{dayLabels[i]} {s.StartTime}-{s.EndTime}");
            }
            WorkingHoursLine1 = string.Join("  |  ", lines.Take(3));
            WorkingHoursLine2 = string.Join("  |  ", lines.Skip(3).Take(2));
            WorkingHoursLine3 = string.Join("  |  ", lines.Skip(5));
        }
        else if (s.Enabled)
        {
            WorkingHoursLine1 = $"{s.StartTime} - {s.EndTime}";
            WorkingHoursLine2 = "";
            WorkingHoursLine3 = "";
        }
        else
        {
            WorkingHoursLine1 = "24/7";
            WorkingHoursLine2 = "ללא הגבלת שעות";
            WorkingHoursLine3 = "";
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
