using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

public interface IAuthService
{
    UserData? CurrentUser { get; }

    Task<bool> IsLoggedInAsync();
    Task<ServiceResult> LoginAsync(string phone, string password);
    Task<ServiceResult> RegisterAsync(string phone, string password, string firstName, string lastName, string email = "");
    Task LogoutAsync();
    Task<ServiceResult> UpdateUserDataAsync(Dictionary<string, object> updates);
}
