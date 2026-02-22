using System.Globalization;
using System.Windows;
using System.Windows.Controls;

namespace SionyxKiosk.Views.Controls;

public partial class PurchaseCard : UserControl
{
    public static readonly DependencyProperty PackageNameProperty =
        DependencyProperty.Register(nameof(PackageName), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty PurchaseDateProperty =
        DependencyProperty.Register(nameof(PurchaseDate), typeof(string), typeof(PurchaseCard),
            new PropertyMetadata("", OnPurchaseDateChanged));

    public static readonly DependencyProperty AmountProperty =
        DependencyProperty.Register(nameof(Amount), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty StatusProperty =
        DependencyProperty.Register(nameof(Status), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty MinutesProperty =
        DependencyProperty.Register(nameof(Minutes), typeof(int), typeof(PurchaseCard),
            new PropertyMetadata(0, OnDetailChanged));

    public static readonly DependencyProperty PrintBudgetProperty =
        DependencyProperty.Register(nameof(PrintBudget), typeof(double), typeof(PurchaseCard),
            new PropertyMetadata(0.0, OnDetailChanged));

    public static readonly DependencyProperty ValidityDaysProperty =
        DependencyProperty.Register(nameof(ValidityDays), typeof(int), typeof(PurchaseCard),
            new PropertyMetadata(0, OnDetailChanged));

    public static readonly DependencyProperty FormattedDateProperty =
        DependencyProperty.Register(nameof(FormattedDate), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty MinutesDisplayProperty =
        DependencyProperty.Register(nameof(MinutesDisplay), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty PrintsDisplayProperty =
        DependencyProperty.Register(nameof(PrintsDisplay), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty ValidityDisplayProperty =
        DependencyProperty.Register(nameof(ValidityDisplay), typeof(string), typeof(PurchaseCard), new PropertyMetadata(""));

    public static readonly DependencyProperty HasMinutesProperty =
        DependencyProperty.Register(nameof(HasMinutes), typeof(Visibility), typeof(PurchaseCard), new PropertyMetadata(Visibility.Collapsed));

    public static readonly DependencyProperty HasPrintsProperty =
        DependencyProperty.Register(nameof(HasPrints), typeof(Visibility), typeof(PurchaseCard), new PropertyMetadata(Visibility.Collapsed));

    public static readonly DependencyProperty HasValidityProperty =
        DependencyProperty.Register(nameof(HasValidity), typeof(Visibility), typeof(PurchaseCard), new PropertyMetadata(Visibility.Collapsed));

    public string PackageName { get => (string)GetValue(PackageNameProperty); set => SetValue(PackageNameProperty, value); }
    public string PurchaseDate { get => (string)GetValue(PurchaseDateProperty); set => SetValue(PurchaseDateProperty, value); }
    public string Amount { get => (string)GetValue(AmountProperty); set => SetValue(AmountProperty, value); }
    public string Status { get => (string)GetValue(StatusProperty); set => SetValue(StatusProperty, value); }
    public int Minutes { get => (int)GetValue(MinutesProperty); set => SetValue(MinutesProperty, value); }
    public double PrintBudget { get => (double)GetValue(PrintBudgetProperty); set => SetValue(PrintBudgetProperty, value); }
    public int ValidityDays { get => (int)GetValue(ValidityDaysProperty); set => SetValue(ValidityDaysProperty, value); }
    public string FormattedDate { get => (string)GetValue(FormattedDateProperty); set => SetValue(FormattedDateProperty, value); }
    public string MinutesDisplay { get => (string)GetValue(MinutesDisplayProperty); set => SetValue(MinutesDisplayProperty, value); }
    public string PrintsDisplay { get => (string)GetValue(PrintsDisplayProperty); set => SetValue(PrintsDisplayProperty, value); }
    public string ValidityDisplay { get => (string)GetValue(ValidityDisplayProperty); set => SetValue(ValidityDisplayProperty, value); }
    public Visibility HasMinutes { get => (Visibility)GetValue(HasMinutesProperty); set => SetValue(HasMinutesProperty, value); }
    public Visibility HasPrints { get => (Visibility)GetValue(HasPrintsProperty); set => SetValue(HasPrintsProperty, value); }
    public Visibility HasValidity { get => (Visibility)GetValue(HasValidityProperty); set => SetValue(HasValidityProperty, value); }

    public PurchaseCard() { InitializeComponent(); }

    private static void OnPurchaseDateChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is not PurchaseCard card) return;
        var raw = e.NewValue as string ?? "";
        if (DateTime.TryParse(raw, CultureInfo.InvariantCulture, DateTimeStyles.None, out var dt))
            card.FormattedDate = dt.ToString("dd/MM/yyyy HH:mm", CultureInfo.InvariantCulture);
        else
            card.FormattedDate = raw;
    }

    private static void OnDetailChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is not PurchaseCard card) return;

        var minutes = card.Minutes;
        if (minutes > 0)
        {
            card.HasMinutes = Visibility.Visible;
            if (minutes >= 60)
            {
                var hours = minutes / 60;
                var remaining = minutes % 60;
                card.MinutesDisplay = remaining > 0 ? $"{hours} שעות ו-{remaining} דקות" : $"{hours} שעות";
            }
            else
            {
                card.MinutesDisplay = $"{minutes} דקות";
            }
        }
        else
        {
            card.HasMinutes = Visibility.Collapsed;
        }

        var prints = card.PrintBudget;
        if (prints > 0)
        {
            card.HasPrints = Visibility.Visible;
            card.PrintsDisplay = $"₪{prints:F0} הדפסות";
        }
        else
        {
            card.HasPrints = Visibility.Collapsed;
        }

        var validity = card.ValidityDays;
        if (validity > 0)
        {
            card.HasValidity = Visibility.Visible;
            card.ValidityDisplay = validity switch
            {
                1 => "יום אחד",
                7 => "שבוע",
                14 => "שבועיים",
                30 => "חודש",
                _ => $"{validity} ימים",
            };
        }
        else
        {
            card.HasValidity = Visibility.Collapsed;
        }
    }
}
