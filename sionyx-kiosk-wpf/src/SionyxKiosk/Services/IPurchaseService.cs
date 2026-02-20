using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

public interface IPurchaseService
{
    Task<ServiceResult> CreatePendingPurchaseAsync(string userId, Package package);
    Task<ServiceResult> GetPurchaseStatusAsync(string purchaseId);
    Task<ServiceResult> GetUserPurchaseHistoryAsync(string userId);
    Task<ServiceResult> GetPurchaseStatisticsAsync(string userId);
}
