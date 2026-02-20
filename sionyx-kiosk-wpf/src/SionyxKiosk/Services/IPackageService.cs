namespace SionyxKiosk.Services;

public interface IPackageService
{
    Task<ServiceResult> GetAllPackagesAsync();
    Task<ServiceResult> GetPackageByIdAsync(string packageId);
}
