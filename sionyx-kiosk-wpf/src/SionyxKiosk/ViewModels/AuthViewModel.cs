using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using SionyxKiosk.Services;

namespace SionyxKiosk.ViewModels;

/// <summary>Auth ViewModel: login, register, password reset.</summary>
public partial class AuthViewModel : ObservableObject
{
    private readonly AuthService _auth;

    [ObservableProperty] private string _phone = "";
    [ObservableProperty] private string _password = "";
    [ObservableProperty] private string _firstName = "";
    [ObservableProperty] private string _lastName = "";
    [ObservableProperty] private string _email = "";
    [ObservableProperty] private string _errorMessage = "";
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private bool _isLoginMode = true;

    public event Action? LoginSucceeded;
    public event Action? RegistrationSucceeded;

    public AuthViewModel(AuthService auth)
    {
        _auth = auth;
    }

    [RelayCommand]
    private async Task LoginAsync()
    {
        if (string.IsNullOrWhiteSpace(Phone) || string.IsNullOrWhiteSpace(Password))
        {
            ErrorMessage = "אנא מלא את כל השדות";
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
    }

    /// <summary>Called by App when auto-login succeeds.</summary>
    public void TriggerAutoLogin() => LoginSucceeded?.Invoke();
}
