from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from sales.models import Sale
from shops.models import BusinessPeriodConfig, BusinessPerformanceHistory

class Command(BaseCommand):
    help = "Calculate business performance at the end of a period"

    def handle(self, *args, **kwargs):
        try:
            # Fetch period settings
            period_config = BusinessPeriodConfig.objects.get(id=1)
            last_calculation_date = period_config.last_calculation_date
            next_calculation_date = period_config.next_calculation_date()

            # Ensure we are at the end of a period
            if now().date() < next_calculation_date:
                self.stdout.write(self.style.WARNING("Not yet time to calculate business performance."))
                return

            # Get sales within the period
            sales = Sale.objects.filter(date__gte=last_calculation_date, date__lt=next_calculation_date)

            # Initialize totals
            total_cash_sales = 0
            total_credit_sales = 0
            total_partial_payments = 0
            total_profit = 0
            carried_forward_credit = 0

            # Categorize sales
            for sale in sales:
                if sale.payment_status == "paid":
                    total_cash_sales += sale.grand_total
                    total_profit += sale.profit
                elif sale.payment_status == "credit":
                    total_credit_sales += sale.balance
                    carried_forward_credit += sale.balance
                elif sale.payment_status == "partial":
                    total_partial_payments += sale.amount_paid
                    total_profit += sale.profit * (sale.amount_paid / sale.grand_total)
                    carried_forward_credit += sale.balance  # Remaining balance is still credit

            # Save the period report
            BusinessPerformanceHistory.objects.create(
                period_start=last_calculation_date,
                period_end=next_calculation_date,
                total_cash_sales=total_cash_sales,
                total_credit_sales=total_credit_sales,
                total_partial_payments=total_partial_payments,
                total_profit=total_profit,
                carried_forward_credit=carried_forward_credit
            )

            # Update next period
            period_config.last_calculation_date = next_calculation_date
            period_config.save()

            self.stdout.write(self.style.SUCCESS("Business performance calculated successfully!"))

        except BusinessPeriodConfig.DoesNotExist:
            self.stdout.write(self.style.ERROR("Business period configuration not found!"))
