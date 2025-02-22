from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now
from django.db.models import Sum, Count, F
from django.http import JsonResponse, HttpResponse
import csv

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import BalanceSheet
from sales.models import Sale, SaleItem
from inventory.models import Product
from .models import SalesReport, ProductPerformanceReport, AccountingReport


# --- ROLE CHECK FUNCTIONS ---
def is_superadmin(user):
    return user.is_authenticated and user.role == "superadmin"

def is_manager(user):
    return user.is_authenticated and user.role == "manager"

def is_superadmin_or_manager(user):
    return user.is_authenticated and (user.role == "superadmin" or user.role == "manager")


# --- REPORT GENERATION FUNCTIONS ---
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

    ProductPerformanceReport.objects.all().delete()  # Avoid duplicate records

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


# --- REPORT VIEWS ---
@login_required
@user_passes_test(is_superadmin_or_manager)
def sales_report_view(request):
    """View to display sales reports."""
    reports = SalesReport.objects.all().order_by('-date')
    return render(request, 'reports/reports.html', {'reports': reports})


@login_required
@user_passes_test(is_superadmin_or_manager)
def product_performance_view(request):
    """View to display product performance (top & least selling products)."""
    products = ProductPerformanceReport.objects.all().order_by('-quantity_sold')
    return render(request, 'reports/reports.html', {'products': products})


@login_required
@user_passes_test(is_superadmin_or_manager)
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
    """Fetch reports data dynamically for dashboards."""
    sales = Sale.objects.values("date").annotate(total_sales=Sum("total_amount"))
    profits = Sale.objects.values("date").annotate(total_profit=Sum("profit"))

    top_selling = Product.objects.annotate(sales_count=Count("saleitem")).order_by("-sales_count")[:5]
    least_selling = Product.objects.annotate(sales_count=Count("saleitem")).order_by("sales_count")[:5]

    return JsonResponse({
        "sales_dates": [s["date"] for s in sales],
        "sales_amounts": [s["total_sales"] for s in sales],
        "profit_amounts": [p["total_profit"] for p in profits],
        "top_selling": [{"name": p.name, "sales_count": p.sales_count} for p in top_selling],
        "least_selling": [{"name": p.name, "sales_count": p.sales_count} for p in least_selling]
    })


# --- EXPORT CSV FUNCTION ---
@login_required
@user_passes_test(is_superadmin)
def export_sales_csv(request):
    """Export sales data as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Seller', 'Total Amount', 'Date'])

    sales = Sale.objects.all().values_list("id", "seller__username", "total_amount", "date")
    for sale in sales:
        writer.writerow(sale)

    return response


# --- DASHBOARD REPORTS ---
@login_required
@user_passes_test(is_superadmin_or_manager)
def reports_dashboard(request):
    """Superadmin and Manager Reports Dashboard."""
    today = now().date()

    # Sales Reports
    sales_reports = SalesReport.objects.filter(date=today)
    total_sales = Sale.objects.filter(date_sold=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Profit Analysis
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

    # Daily Sales Summary
    summarized_reports = {
        "total_sales": total_sales,
        "total_profit": SaleItem.objects.filter(sale__date_sold=today).aggregate(
            total_profit=Sum(F('selling_price') - F('entry_price'))
        )['total_profit'] or 0,
    }

    context = {
        "sales_reports": sales_reports,
        "profit_data": profit_data,
        "summarized_reports": summarized_reports
    }

    return render(request, "reports/reports.html", context)


def export_sales_pdf(request):
    """ Generate a PDF file containing sales reports """
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'

    # Create a PDF document
    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle("Sales Report")

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Sales Report")
    
    # Table headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Product")
    pdf.drawString(200, 700, "Seller")
    pdf.drawString(350, 700, "Total Amount")
    pdf.drawString(500, 700, "Date")

    sales = Sale.objects.all().order_by("-date")
    y = 680  # Y-coordinate for table rows

    # Add sales data to PDF
    pdf.setFont("Helvetica", 12)
    for sale in sales:
        pdf.drawString(50, y, sale.product.name)
        pdf.drawString(200, y, sale.seller.username)
        pdf.drawString(350, y, f"${sale.total_price:.2f}")
        pdf.drawString(500, y, sale.date.strftime("%Y-%m-%d"))
        y -= 20

        # Create a new page if needed
        if y < 50:
            pdf.showPage()
            y = 750  # Reset position

    pdf.showPage()
    pdf.save()
    return response


def export_balance_csv(request):
    """ Export balance sheet as CSV """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="balance_sheet.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Total Revenue", "Total Expenses", "Net Profit"])

    balances = BalanceSheet.objects.all().order_by("-date")
    for balance in balances:
        writer.writerow([balance.date, balance.total_revenue, balance.total_expenses, balance.net_profit])

    return response


def export_balance_pdf(request):
    """ Generate a PDF file containing balance sheet reports """
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="balance_sheet.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle("Balance Sheet Report")

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Balance Sheet Report")

    # Table headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 700, "Date")
    pdf.drawString(200, 700, "Total Revenue")
    pdf.drawString(350, 700, "Total Expenses")
    pdf.drawString(500, 700, "Net Profit")

    balances = BalanceSheet.objects.all().order_by("-date")
    y = 680  # Y-coordinate for table rows

    # Add balance sheet data to PDF
    pdf.setFont("Helvetica", 12)
    for balance in balances:
        pdf.drawString(50, y, balance.date.strftime("%Y-%m-%d"))
        pdf.drawString(200, y, f"${balance.total_revenue:.2f}")
        pdf.drawString(350, y, f"${balance.total_expenses:.2f}")
        pdf.drawString(500, y, f"${balance.net_profit:.2f}")
        y -= 20

        # Create a new page if needed
        if y < 50:
            pdf.showPage()
            y = 750  # Reset position

    pdf.showPage()
    pdf.save()
    return response
