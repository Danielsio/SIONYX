using System.Threading.Tasks;
using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

public interface IPaymentDialogFactory
{
    (bool Succeeded, object? Dialog) CreateAndShow(Package package, System.Windows.Window? owner = null);

    /// <summary>True if the signed-in user has a saved card (enables one-click pay).</summary>
    Task<bool> HasSavedCardAsync();

    /// <summary>
    /// Charge the user's saved card for <paramref name="package"/> via the server, then
    /// wait for the gateway callback to credit it. Returns true on confirmed success.
    /// </summary>
    Task<bool> ChargeWithSavedCardAsync(Package package);
}
