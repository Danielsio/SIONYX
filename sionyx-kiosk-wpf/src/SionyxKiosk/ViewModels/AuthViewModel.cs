using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Auth ViewModel: login, register, password reset.</summary>
public partial class AuthViewModel : ObservableObject
{
    private readonly AuthService _auth;
    private readonly OrganizationMetadataService? _metadataService;

    [ObservableProperty] private string _phone = "";
    [ObservableProperty] private string _password = "";
    [ObservableProperty] private string _firstName = "";
    [ObservableProperty] private string _lastName = "";
    [ObservableProperty] private string _email = "";
    [ObservableProperty] private string _errorMessage = "";
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private bool _isLoginMode = true;
    [ObservableProperty] private string _forgotPasswordInfo = "";

    /// <summary>Org-branded login background (empty = the built-in look). Bound by AuthWindow.</summary>
    [ObservableProperty] private string _backgroundImageUrl = "";

    /// <summary>Dynamic button text that changes during loading.</summary>
    public string LoginButtonText => IsLoading ? "מתחבר..." : "התחבר";
    public string RegisterButtonText => IsLoading ? "נרשם..." : "הירשם";

    partial void OnIsLoadingChanged(bool value)
    {
        OnPropertyChanged(nameof(LoginButtonText));
        OnPropertyChanged(nameof(RegisterButtonText));
    }

    public event Action? LoginSucceeded;
    public event Action? RegistrationSucceeded;

    public AuthViewModel(AuthService auth, OrganizationMetadataService? metadataService = null)
    {
        _auth = auth;
        _metadataService = metadataService;
    }

    /// <summary>
    /// Fetch the org's login branding. Best-effort: any failure or a missing/
    /// invalid URL just leaves the built-in background. Called when the auth
    /// screen appears (and can be re-called to live-refresh).
    /// </summary>
    [RelayCommand]
    public async Task LoadBrandingAsync()
    {
        if (_metadataService == null) return;
        try
        {
            var settings = await _metadataService.GetKioskSettingsAsync();
            BackgroundImageUrl = settings.HasUsableBackground ? settings.BackgroundUrl : "";
        }
        catch
        {
            BackgroundImageUrl = "";
        }
    }

    private static bool IsValidPhone(string phone)
    {
        var digits = phone.Replace("-", "").Replace(" ", "").Trim();
        return digits.Length >= 9 && digits.Length <= 12 && digits.All(char.IsDigit);
    }

    [RelayCommand]
    private async Task LoginAsync()
    {
        if (string.IsNullOrWhiteSpace(Phone) || string.IsNullOrWhiteSpace(Password))
        {
            ErrorMessage = "אנא מלא את כל השדות";
            return;
        }

        if (!IsValidPhone(Phone))
        {
            ErrorMessage = "מספר טלפון לא תקין";
            return;
        }

        IsLoading = true;
        ErrorMessage = "";

        var result = await _auth.LoginAsync(Phone, Password);
        IsLoading = false;

        if (result.IsSuccess)
            LoginSucceeded?.Invoke();
        else
            ErrorMessage = result.Error ?? "שגיאת התחברות";
    }

    [RelayCommand]
    private async Task RegisterAsync()
    {
        if (string.IsNullOrWhiteSpace(Phone) || string.IsNullOrWhiteSpace(Password) ||
            string.IsNullOrWhiteSpace(FirstName) || string.IsNullOrWhiteSpace(LastName))
        {
            ErrorMessage = "אנא מלא את כל השדות";
            return;
        }

        if (!IsValidPhone(Phone))
        {
            ErrorMessage = "מספר טלפון לא תקין";
            return;
        }

        if (Password.Length < 6)
        {
            ErrorMessage = "הסיסמה חייבת להכיל לפחות 6 תווים";
            return;
        }

        IsLoading = true;
        ErrorMessage = "";

        var result = await _auth.RegisterAsync(Phone, Password, FirstName, LastName, Email);
        IsLoading = false;

        if (result.IsSuccess)
            RegistrationSucceeded?.Invoke();
        else
            ErrorMessage = result.Error ?? "שגיאת הרשמה";
    }

    [RelayCommand]
    private void ToggleMode()
    {
        IsLoginMode = !IsLoginMode;
        ErrorMessage = "";
        ForgotPasswordInfo = "";
    }

    [RelayCommand]
    private async Task ForgotPasswordAsync()
    {
        if (_metadataService == null)
        {
            ForgotPasswordInfo = "לא ניתן לטעון פרטי קשר. פנה למנהל המערכת.";
            return;
        }

        IsLoading = true;
        try
        {
            var result = await _metadataService.GetAdminContactAsync();
            if (result.IsSuccess && result.Data is { } contact)
            {
                var type = contact.GetType();
                var phone = type.GetProperty("phone")?.GetValue(contact)?.ToString() ?? "";
                var email = type.GetProperty("email")?.GetValue(contact)?.ToString() ?? "";

                var info = "לאיפוס סיסמה פנה למנהל:";
                if (!string.IsNullOrEmpty(phone)) info += $"\n📞 {phone}";
                if (!string.IsNullOrEmpty(email)) info += $"\n✉️ {email}";
                ForgotPasswordInfo = info;
            }
            else
            {
                ForgotPasswordInfo = "פנה למנהל המערכת לאיפוס סיסמה.";
            }
        }
        catch
        {
            ForgotPasswordInfo = "פנה למנהל המערכת לאיפוס סיסמה.";
        }
        finally
        {
            IsLoading = false;
        }
    }

    /// <summary>Called by App when auto-login succeeds.</summary>
    public void TriggerAutoLogin() => LoginSucceeded?.Invoke();
}
