from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from django.db.models import Sum, Count, F
from sales.models import Sale, SaleItem
from .models import SalesReport, ProductPerformanceReport, AccountingReport
from inventory.models import Product  # Adjust the import path as necessary
from django.http import JsonResponse
from sales.models import CreditSale
import csv
from django.http import HttpResponse

def is_superadmin_or_manager(user):
    return user.is_authenticated and (user.role == "superadmin" or user.role == "manager")


def generate_sales_report():
    """Generates and saves daily sales report."""
    today = now().date()
    sales_data = Sale.objects.filter(date_sold=today).aggregate(
        total_sales=Sum('total_amount')
    )
    profit_data = SaleItem.objects.filter(sale__date_sold=today).aggregate(
        total_profit=Sum(F('selling_price') - F('entry_price'))
    )
    
    report = SalesReport.objects.create(
        date=today,
        total_sales=sales_data['total_sales'] or 0,
        total_profit=profit_data['total_profit'] or 0
    )
    return report

def generate_product_performance_report():
    """Generates product performance reports."""
    products = SaleItem.objects.values('product__name').annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum('selling_price')
    ).order_by('-quantity_sold')

    for product in products:
        ProductPerformanceReport.objects.create(
            product_name=product['product__name'],
            quantity_sold=product['quantity_sold'],
            total_revenue=product['total_revenue']
        )

def generate_accounting_report():
    """Generates an accounting report including balance sheet."""
    today = now().date()
    total_credit_sales = Sale.objects.filter(is_credit=True, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_cash_sales = Sale.objects.filter(is_credit=False, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_profit = SaleItem.objects.filter(sale__date_sold=today).aggregate(Sum(F('selling_price') - F('entry_price')))['total_profit'] or 0

    balance_sheet = f"Total Cash Sales: {total_cash_sales}, Total Credit Sales: {total_credit_sales}, Total Profit: {total_profit}"
    
    AccountingReport.objects.create(
        date=today,
        total_credit_sales=total_credit_sales,
        total_cash_sales=total_cash_sales,
        total_profit=total_profit,
        balance_sheet=balance_sheet
    )
def sales_report_view(request):
    """View to display sales reports."""
    reports = SalesReport.objects.all().order_by('-date')
    return render(request, 'reports/reports.html', {'reports': reports})

def product_performance_view(request):
    """View to display top and least selling products."""
    products = ProductPerformanceReport.objects.all().order_by('-quantity_sold')
    return render(request, 'reports/reports.html', {'products': products})

def accounting_report_view(request):
    """View to display accounting reports."""
    reports = AccountingReport.objects.all().order_by('-date')
    return render(request, 'reports/reports.html', {'reports': reports})

@login_required
@user_passes_test(is_superadmin_or_manager)
def profit_analysis(request):
    """Calculate profit based on entry price vs selling price."""
    products = Product.objects.all()
    profit_data = []

    for product in products:
        sales = SaleItem.objects.filter(product=product)
        revenue = sales.aggregate(total_revenue=Sum(F('quantity') * F('selling_price')))['total_revenue'] or 0
        cost = sales.aggregate(total_cost=Sum(F('quantity') * F('product__entry_price')))['total_cost'] or 0
        profit = revenue - cost

        profit_data.append({
            "product": product.name,
            "total_sold": sales.aggregate(total_sold=Sum('quantity'))['total_sold'] or 0,
            "total_revenue": revenue,
            "total_profit": profit
        })

    return render(request, "reports/reports.html", {"profit_data": profit_data})



@login_required
def reports_data(request):
    """ Fetches reports data dynamically for dashboards """
    sales = Sale.objects.values("date").annotate(total_sales=Sum("total_amount"))
    profits = Sale.objects.values("date").annotate(total_profit=Sum("profit"))

    top_selling = Product.objects.annotate(sales_count=Count("saleitem")).order_by("-sales_count")[:5]
    least_selling = Product.objects.annotate(sales_count=Count("saleitem")).order_by("sales_count")[:5]

    credit_sales = CreditSale.objects.values("customer", "amount_due", "status")

    return JsonResponse({
        "sales_dates": [s["date"] for s in sales],
        "sales_amounts": [s["total_sales"] for s in sales],
        "profit_amounts": [p["total_profit"] for p in profits],
        "top_selling": [{"name": p.name, "sales_count": p.sales_count} for p in top_selling],
        "least_selling": [{"name": p.name, "sales_count": p.sales_count} for p in least_selling],
        "credit_sales": list(credit_sales)
    })


def is_superadmin(user):
    return user.is_authenticated and user.role == "superadmin"

def is_manager(user):
    return user.is_authenticated and user.role == "manager"

@login_required
@user_passes_test(is_superadmin)
def reports_dashboard(request):
    """Superadmin Reports Dashboard"""
    sales = Sale.objects.all()
    total_sales = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_credit_sales = CreditSale.objects.aggregate(Sum('amount_due'))['amount_due__sum'] or 0

    # Top-selling products
    top_products = SaleItem.objects.values("product__name").annotate(
        total_sold=Sum("quantity")
    ).order_by("-total_sold")[:5]

    # Least-selling products
    least_products = SaleItem.objects.values("product__name").annotate(
        total_sold=Sum("quantity")
    ).order_by("total_sold")[:5]

    context = {
        "total_sales": total_sales,
        "total_credit_sales": total_credit_sales,
        "top_products": top_products,
        "least_products": least_products,
    }
    return render(request, "reports/reports.html", context)


@login_required
@user_passes_test(is_manager)
def manager_reports(request):
    """Manager Reports - Only for products under their management"""
    sales = Sale.objects.filter(shop__manager=request.user)
    total_sales = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Filter by shop (if necessary)
    shop_id = request.GET.get("shop")
    if shop_id:
        sales = sales.filter(shop_id=shop_id)

    context = {
        "total_sales": total_sales,
        "sales": sales,
    }
    return render(request, "reports/reports.html", context)


@login_required
@user_passes_test(is_superadmin)
def export_sales_csv(request):
    """Export sales data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Seller', 'Total Amount', 'Date'])

    sales = Sale.objects.all().values_list("id", "seller__username", "total_amount", "date")
    for sale in sales:
        writer.writerow(sale)

    return response



# --- Helper functions for role checks ---
def is_superadmin(user):
    return user.is_authenticated and user.role == "superadmin"

def is_manager(user):
    return user.is_authenticated and user.role == "manager"

def is_superadmin_or_manager(user):
    return user.is_authenticated and (user.role == "superadmin" or user.role == "manager")


# --- Report Generation Functions (if needed) ---
def generate_sales_report():
    """Generates and saves daily sales report."""
    today = now().date()
    sales_data = Sale.objects.filter(date_sold=today).aggregate(
        total_sales=Sum('total_amount')
    )
    profit_data = SaleItem.objects.filter(sale__date_sold=today).aggregate(
        total_profit=Sum(F('selling_price') - F('entry_price'))
    )
    
    report = SalesReport.objects.create(
        date=today,
        total_sales=sales_data['total_sales'] or 0,
        total_profit=profit_data['total_profit'] or 0
    )
    return report

def generate_product_performance_report():
    """Generates product performance reports."""
    products = SaleItem.objects.values('product__name').annotate(
        quantity_sold=Sum('quantity'),
        total_revenue=Sum('selling_price')
    ).order_by('-quantity_sold')

    for product in products:
        ProductPerformanceReport.objects.create(
            product_name=product['product__name'],
            quantity_sold=product['quantity_sold'],
            total_revenue=product['total_revenue']
        )

def generate_accounting_report():
    """Generates an accounting report including balance sheet."""
    today = now().date()
    total_credit_sales = Sale.objects.filter(is_credit=True, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_cash_sales = Sale.objects.filter(is_credit=False, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_profit = SaleItem.objects.filter(sale__date_sold=today).aggregate(Sum(F('selling_price') - F('entry_price')))['total_profit'] or 0

    balance_sheet = f"Total Cash Sales: {total_cash_sales}, Total Credit Sales: {total_credit_sales}, Total Profit: {total_profit}"
    
    AccountingReport.objects.create(
        date=today,
        total_credit_sales=total_credit_sales,
        total_cash_sales=total_cash_sales,
        total_profit=total_profit,
        balance_sheet=balance_sheet
    )

# --- Main Reports Dashboard View ---
@login_required
@user_passes_test(is_superadmin_or_manager)
def reports_dashboard(request):
    today = now().date()

    # Sales Reports (daily)
    sales_reports = SalesReport.objects.filter(date=today).order_by('-date')
    total_sales = Sale.objects.filter(date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Profit Analysis across all products
    products = Product.objects.all()
    profit_data = []
    for product in products:
        sales = SaleItem.objects.filter(product=product)
        revenue = sales.aggregate(total_revenue=Sum(F('quantity') * F('selling_price')))['total_revenue'] or 0
        cost = sales.aggregate(total_cost=Sum(F('quantity') * F('product__entry_price')))['total_cost'] or 0
        profit = revenue - cost
        profit_data.append({
            "product": product.name,
            "total_sold": sales.aggregate(total_sold=Sum('quantity'))['total_sold'] or 0,
            "total_revenue": revenue,
            "total_profit": profit
        })

    # Credit Sales Data
    credit_sales = CreditSale.objects.filter(date_sold=today)
    credit_profit = credit_sales.aggregate(total=Sum('profit'))['total'] or 0  # Adjust field as needed

    # Daily Profits Data
    daily_net_profit = total_sales  # Simplified; adjust calculation as needed
    daily_paid_profit = Sale.objects.filter(is_credit=False, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Shop Analysis Data (Assumes each Sale has a ForeignKey to Shop)
    # Example: group sales by shop, calculate totals
    shop_analysis = Sale.objects.filter(date_sold=today).values("shop__name").annotate(
        total_sales=Sum('total_amount'),
        total_profit=Sum(F('profit'))
    ).order_by("-total_sales")
    best_selling_shops = shop_analysis  # For demonstration; adjust as needed

    # Summarized Reports: We'll assume this is an aggregation of sales & profit.
    summarized_reports = {
        "total_sales": total_sales,
        "total_profit": SaleItem.objects.filter(sale__date_sold=today).aggregate(
            total_profit=Sum(F('selling_price') - F('entry_price'))
        )['total_profit'] or 0,
    }

    # Balance Sheet Data (dummy values; adjust with your actual logic)
    total_cash_sales = Sale.objects.filter(is_credit=False, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_credit_sales = Sale.objects.filter(is_credit=True, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_liabilities = total_credit_sales  # Simplified assumption
    net_worth = total_cash_sales - total_liabilities
    balance_sheet = {
        "total_assets": total_cash_sales,
        "total_liabilities": total_liabilities,
        "net_worth": net_worth,
    }

    # Current Stock Cost Data
    # Assuming that each product has a cost (entry_price) and that when sold, cash is received equal to selling price
    current_stock_cash = Sale.objects.filter(is_credit=False, date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    # This is the cash from sold stock. Remaining stock cost can be calculated if needed.
    remaining_stock_cost = sum([p.stock_quantity * p.entry_price for p in products]) - current_stock_cash

    # Data for Sales Trends Chart
    sales_data_qs = Sale.objects.filter(date_sold=today).values("date_sold").annotate(total_sales=Sum('total_amount')).order_by("date_sold")
    sales_dates = [str(item["date_sold"]) for item in sales_data_qs]
    sales_values = [item["total_sales"] for item in sales_data_qs]

    context = {
        "sales_reports": sales_reports,
        "total_sales": total_sales,
        "profit_data": profit_data,
        "credit_sales": credit_sales,
        "credit_profit": credit_profit,
        "daily_net_profit": daily_net_profit,
        "daily_paid_profit": daily_paid_profit,
        "shop_analysis": shop_analysis,
        "best_selling_shops": best_selling_shops,
        "summarized_reports": summarized_reports,
        "balance_sheet": balance_sheet,
        "current_stock_cash": current_stock_cash,
        "remaining_stock_cost": remaining_stock_cost,
        "sales_dates": sales_dates,
        "sales_values": sales_values,
    }
    return render(request, "reports/reports.html", context)


# --- Data API for Reports (for Chart.js integration) ---
@login_required
def reports_data(request):
    sales = Sale.objects.values("date_sold").annotate(total_sales=Sum("total_amount"))
    profits = Sale.objects.values("date_sold").annotate(total_profit=Sum("profit"))

    top_selling = Product.objects.annotate(sales_count=Count("saleitem")).order_by("-sales_count")[:5]
    least_selling = Product.objects.annotate(sales_count=Count("saleitem")).order_by("sales_count")[:5]

    credit_sales = CreditSale.objects.values("customer", "amount_due", "status")

    return JsonResponse({
        "sales_dates": [s["date_sold"] for s in sales],
        "sales_amounts": [s["total_sales"] for s in sales],
        "profit_amounts": [p["total_profit"] for p in profits],
        "top_selling": [{"name": p.name, "sales_count": p.sales_count} for p in top_selling],
        "least_selling": [{"name": p.name, "sales_count": p.sales_count} for p in least_selling],
        "credit_sales": list(credit_sales)
    })


# --- Export Reports Functions ---
@login_required
@user_passes_test(is_superadmin_or_manager)
def export_sales_csv(request):
    """Export sales data as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Seller', 'Total Amount', 'Date Sold'])

    sales = Sale.objects.all().values_list("id", "seller__username", "total_amount", "date_sold")
    for sale in sales:
        writer.writerow(sale)

    return response


@login_required
@user_passes_test(is_superadmin_or_manager)
def export_sales_pdf(request):
    # Placeholder function: Replace with actual PDF generation logic.
    response = HttpResponse("PDF export is not implemented yet.", content_type="text/plain")
    return response


@login_required
@user_passes_test(is_superadmin_or_manager)
def export_balance_csv(request):
    """Export balance sheet data as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="balance_sheet.csv"'

    writer = csv.writer(response)
    writer.writerow(['Total Assets', 'Total Liabilities', 'Net Worth'])
    bs = AccountingReport.objects.last()  # Assuming the latest report
    if bs:
        writer.writerow([bs.total_cash_sales, bs.total_credit_sales, bs.total_profit])
    else:
        writer.writerow(["N/A", "N/A", "N/A"])
    return response

@login_required
@user_passes_test(is_superadmin_or_manager)
def export_balance_pdf(request):
    # Placeholder function: Replace with actual PDF generation logic.
    response = HttpResponse("Balance sheet PDF export is not implemented yet.", content_type="text/plain")
    return response
