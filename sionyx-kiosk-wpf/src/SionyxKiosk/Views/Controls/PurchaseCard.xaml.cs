using System.Windows;
using System.Windows.Controls;

namespace SionyxKiosk.Views.Controls;

public partial class PurchaseCard : UserControl
{
    public static readonly DependencyProperty PackageNameProperty =
        DependencyProperty.Register(nameof(PackageName), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty PurchaseDateProperty =
        DependencyProperty.Register(nameof(PurchaseDate), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty AmountProperty =
        DependencyProperty.Register(nameof(Amount), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty StatusProperty =
        DependencyProperty.Register(nameof(Status), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public string PackageName { get => (string)GetValue(PackageNameProperty); set => SetValue(PackageNameProperty, value); }
    public string PurchaseDate { get => (string)GetValue(PurchaseDateProperty); set => SetValue(PurchaseDateProperty, value); }
    public string Amount { get => (string)GetValue(AmountProperty); set => SetValue(AmountProperty, value); }
    public string Status { get => (string)GetValue(StatusProperty); set => SetValue(StatusProperty, value); }

    public PurchaseCard() { InitializeComponent(); }
}
