using SionyxKiosk.Models;

namespace SionyxKiosk.Services;

public interface IPaymentDialogFactory
{
    (bool Succeeded, object? Dialog) CreateAndShow(Package package, System.Windows.Window? owner = null);
}
