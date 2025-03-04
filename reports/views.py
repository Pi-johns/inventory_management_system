from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from sales.models import Sale, SaleItem
from expenses.models import Expense
from sales.models import DamagedGoods
from django.utils.timezone import now
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Case, When, Value, Q
from shops.models import Shop
from sellers.models import Seller
from django.db.models.functions import TruncDate


@login_required
def reports_home(request):
    """Dashboard for viewing business reports with key metrics and graphs."""
    # Get filters from request
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    shop_id = request.GET.get("shop")
    seller_id = request.GET.get("seller")

    # Build the filter query dynamically
    filters = Q()
    
    if date_from:
        filters &= Q(sale_date__gte=date_from)
    if date_to:
        filters &= Q(sale_date__lte=date_to)
    if shop_id:
        filters &= Q(shop_id=shop_id)
    if seller_id:
        filters &= Q(seller_id=seller_id)

    current_period_start = now().replace(day=1)  # Start of the current month

    # ✅ Total Sales Count
    total_sales_count = Sale.objects.filter(sale_date__gte=current_period_start).count()

    # ✅ Total Revenue (Total Sales Amount)
    total_revenue = Sale.objects.filter(sale_date__gte=current_period_start).aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # ✅ Total Cash Sales
    total_cash_sales = Sale.objects.filter(sale_date__gte=current_period_start, payment_status="paid").aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # ✅ Total Credit Sales
    total_credit_sales = Sale.objects.filter(sale_date__gte=current_period_start, payment_status="credit").aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # ✅ Total Partial Sales
    total_partial_sales = Sale.objects.filter(sale_date__gte=current_period_start, payment_status="partial").aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # ✅ Total Expenses
    total_expenses = Expense.objects.filter(date_recorded__gte=current_period_start).aggregate(Sum('amount'))['amount__sum'] or 0

    # ✅ Total Damages
    total_damages = DamagedGoods.objects.filter(date_damaged__gte=current_period_start).aggregate(Sum('total_loss'))['total_loss__sum'] or 0

    # ✅ Realized & Future Profit Calculation
    sales_with_profit = SaleItem.objects.filter(sale__sale_date__gte=current_period_start).annotate(
        entry_price=F("product__entry_price"),
        item_profit=ExpressionWrapper(
            (F("price") - F("entry_price")) * F("quantity"),
            output_field=DecimalField()
        ),
        realized_profit=Case(
            When(sale__payment_status="paid", then=F("item_profit")),  # Fully paid sales
            When(sale__payment_status="partial", then=F("item_profit") * (F("sale__amount_paid") / F("sale__grand_total"))),  # Partial payments
            default=Value(0),
            output_field=DecimalField()
        ),
        future_profit=Case(
            When(sale__payment_status="credit", then=F("item_profit")),  # Unpaid credit sales
            When(sale__payment_status="partial", then=F("item_profit") * (F("sale__balance") / F("sale__grand_total"))),  # Unpaid part of partial payments
            default=Value(0),
            output_field=DecimalField()
        )
    ).aggregate(
        total_cash_profit=Sum(
            Case(When(sale__payment_status="paid", then=F("item_profit")), default=Value(0), output_field=DecimalField())
        ) or 0,
        total_partial_profit=Sum(
            Case(When(sale__payment_status="partial", then=F("item_profit") * (F("sale__amount_paid") / F("sale__grand_total"))), default=Value(0), output_field=DecimalField())
        ) or 0,
        total_credit_unrealized_profit=Sum(
            Case(
                When(sale__payment_status="credit", then=F("item_profit")),
                When(sale__payment_status="partial", then=F("item_profit") * (F("sale__balance") / F("sale__grand_total"))),
                default=Value(0),
                output_field=DecimalField()
            )
        ) or 0
    )

    total_cash_profit = sales_with_profit["total_cash_profit"]
    total_partial_profit = sales_with_profit["total_partial_profit"]
    total_credit_unrealized_profit = sales_with_profit["total_credit_unrealized_profit"]

    # ✅ Net Profit (Ensuring No Negative Loss)
    net_profit = total_cash_profit + total_partial_profit - (total_expenses + total_damages)

    # ✅ Total Loss Logic (Ensuring No Negative Loss)
    if (total_expenses + total_damages) <= (total_cash_profit + total_partial_profit):
        total_loss = 0  # No loss if sales profit covers expenses and damages
    else:
        total_loss = (total_expenses + total_damages) - (total_cash_profit + total_partial_profit)  # Actual loss
    # Calculate total realized profit (already computed as total_cash_profit + total_partial_profit)
    total_realized_profit = total_cash_profit + total_partial_profit
    
    if total_revenue:
        profit_margin = (total_realized_profit / total_revenue) * 100
    else:
        profit_margin = 0
   
    # ✅ Sales & Profit Over Time Data
    sales_data = (
        Sale.objects
        .filter(sale_date__gte=current_period_start)
        .annotate(sale_day=TruncDate("sale_date"))  # Group by date
        .values("sale_day")
        .annotate(
            total_sales=Sum("grand_total"),
            total_profit=Sum(
                ExpressionWrapper(
                    (F("items__price") - F("items__product__entry_price")) * F("items__quantity"),
                    output_field=DecimalField()
                ) * Case(
                    When(payment_status="paid", then=Value(1)),  # Fully paid
                    When(payment_status="partial", then=F("amount_paid") / F("grand_total")),  # Partially paid portion
                    default=Value(0),  # Credit (not realized yet)
                    output_field=DecimalField()
                )
            ),
        )
        .order_by("sale_day")
    )

    sales_dates = [entry["sale_day"].strftime("%Y-%m-%d") for entry in sales_data]
    sales_totals = [float(entry["total_sales"]) for entry in sales_data]
    profit_totals = [float(entry["total_profit"] or 0) for entry in sales_data]
   
    # ✅ Top 5 Best-Selling Products
    product_names = []
    product_sales = []
    top_products = (
        SaleItem.objects
        .values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )
    if top_products:
        product_names = [item["product__name"] for item in top_products]
        product_sales = [item["total_sold"] for item in top_products]
    # Create a zipped list of top products and their sales:
    top_products_list = list(zip(product_names, product_sales))
    # Calculate the maximum sales value (for scaling the progress bar)
    max_product_sales = max(product_sales) if product_sales else 0
    

    # ✅ Pass data to template
    context = {
        "profit_margin": profit_margin,
        "top_products_list": top_products_list,
        "max_product_sales": max_product_sales,
        "total_sales_count": total_sales_count,  # ✅ Total Sales Count
        "total_revenue": total_revenue,  # ✅ Total Revenue
        "total_cash_sales": total_cash_sales,  # ✅ Total Cash Sales
        "total_credit_sales": total_credit_sales,  # ✅ Total Credit Sales
        "total_partial_sales": total_partial_sales,  # ✅ Total Partial Sales
        "total_expenses": total_expenses,  # ✅ Expenses
        "total_damages": total_damages,  # ✅ Damages
        "net_profit": net_profit,  # ✅ Net Profit
        "total_realized_profit": total_cash_profit + total_partial_profit,  # ✅ Profit actually earned
        "total_future_profit": total_credit_unrealized_profit,  # ✅ Profit from unpaid balances
        "total_cash_profit": total_cash_profit,  # ✅ Fully realized profit
        "total_partial_profit": total_partial_profit,  # ✅ Partially realized profit
        "total_credit_unrealized_profit": total_credit_unrealized_profit,  # ✅ Credit unrealized profit
        "sales_dates": sales_dates,  # ✅ Sales Trend Data
        "sales_totals": sales_totals,  # ✅ Sales Chart Data
        "profit_totals": profit_totals,  # ✅ Profit Chart Data
        "product_names": product_names,  # ✅ Top 5 Product Labels
        "product_sales": product_sales,  # ✅ Top 5 Product Sales Data
        "total_loss": total_loss,  # ✅ Adjusted Loss Calculation
        "filters": {
            "date_from": date_from,
            "date_to": date_to,
            "shop_id": shop_id,
            "seller_id": seller_id,
        },
        "shops": Shop.objects.all(),
        "sellers": Seller.objects.all(),

    }

    return render(request, "reports/reports.html", context)

@login_required
def sales_report(request):
    """Generates sales report with filters (date, shop, seller)."""
    start_date = request.GET.get('start_date', now().replace(day=1))  # Default: Start of month
    end_date = request.GET.get('end_date', now())  # Default: Today
    shop = request.GET.get('shop')
    seller = request.GET.get('seller')

    sales = Sale.objects.filter(date__range=[start_date, end_date])

    if shop:
        sales = sales.filter(shop__id=shop)
    if seller:
        sales = sales.filter(seller__id=seller)

    total_sales = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_transactions = sales.count()
    
    context = {
        "sales": sales,
        "total_sales": total_sales,
        "total_transactions": total_transactions,
    }

    return render(request, "reports/sales_report.html", context)


@login_required
def expense_report(request):
    """Generates expense report with filters (date, shop)."""
    start_date = request.GET.get('start_date', now().replace(day=1))
    end_date = request.GET.get('end_date', now())
    shop = request.GET.get('shop')

    expenses = Expense.objects.filter(date_recorded__range=[start_date, end_date])

    if shop:
        expenses = expenses.filter(shop__id=shop)

    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        "expenses": expenses,
        "total_expenses": total_expenses,
    }

    return render(request, "reports/expense_report.html", context)




@login_required
def damage_report(request):
    """Generates damage report with filters (date, shop)."""
    start_date = request.GET.get('start_date', now().replace(day=1))
    end_date = request.GET.get('end_date', now())
    shop = request.GET.get('shop')

    damaged_goods = DamagedGoods.objects.filter(date_damaged__range=[start_date, end_date])

    if shop:
        damaged_goods = damaged_goods.filter(shop__id=shop)

    total_damages = damaged_goods.aggregate(Sum('total_loss'))['total_loss__sum'] or 0
    total_damaged_items = damaged_goods.aggregate(Sum('quantity'))['quantity__sum'] or 0

    context = {
        "damaged_goods": damaged_goods,
        "total_damages": total_damages,
        "total_damaged_items": total_damaged_items,
    }

    return render(request, "reports/damage_report.html", context)




@login_required
def top_products_report(request):
    """Generates a report of the top 5 performing products."""
    start_date = request.GET.get('start_date', now().replace(day=1))
    end_date = request.GET.get('end_date', now())
    shop = request.GET.get('shop')

    sale_items = SaleItem.objects.filter(sale__date__range=[start_date, end_date])

    if shop:
        sale_items = sale_items.filter(sale__shop__id=shop)

    top_products = sale_items.values("product__name").annotate(
        total_sold=Sum("quantity")
    ).order_by("-total_sold")[:5]  # Top 5 products

    context = {
        "top_products": top_products,
    }

    return render(request, "reports/top_products_report.html", context)




@login_required
def net_profit_report(request):
    """Calculates net profit as (Sales Profit - Expenses - Damage Loss)."""
    start_date = request.GET.get('start_date', now().replace(day=1))
    end_date = request.GET.get('end_date', now())
    shop = request.GET.get('shop')

    # Sales Profit (Cash Sales + Partial Profit)
    sales = Sale.objects.filter(date__range=[start_date, end_date])
    if shop:
        sales = sales.filter(shop__id=shop)
    sales_profit = sales.aggregate(Sum("profit"))["profit__sum"] or 0

    # Total Expenses
    expenses = Expense.objects.filter(date_recorded__range=[start_date, end_date])
    if shop:
        expenses = expenses.filter(shop__id=shop)
    total_expenses = expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    # Total Damage Loss
    damages = DamagedGoods.objects.filter(date_damaged__range=[start_date, end_date])
    if shop:
        damages = damages.filter(shop__id=shop)
    total_damages = damages.aggregate(Sum("total_loss"))["total_loss__sum"] or 0

    # Net Profit Calculation
    net_profit = sales_profit - (total_expenses + total_damages)

    context = {
        "sales_profit": sales_profit,
        "total_expenses": total_expenses,
        "total_damages": total_damages,
        "net_profit": net_profit,
    }

    return render(request, "reports/net_profit_report.html", context)




import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

@login_required
def export_sales_csv(request):
    """ Export sales report as CSV """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Shop', 'Seller', 'Customer', 'Total Amount', 'Payment Status', 'Profit'])
    
    sales = Sale.objects.all()
    for sale in sales:
        writer.writerow([
            sale.sale_date.strftime('%Y-%m-%d'),
            sale.shop.name if sale.shop else "N/A",
            sale.seller.username,
            sale.customer_name,
            sale.grand_total,
            sale.payment_status,
            sale.get_total_profit()
        ])
    return response





@login_required
def export_expenses_csv(request):
    """ Export expenses report as CSV """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Recorded By', 'Description', 'Amount'])
    
    expenses = Expense.objects.all()
    for expense in expenses:
        writer.writerow([
            expense.date_recorded.strftime('%Y-%m-%d'),
            expense.recorded_by.username,
            expense.description,
            expense.amount
        ])
    return response





@login_required
def export_damaged_goods_csv(request):
    """ Export damaged goods report as CSV """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="damaged_goods_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date Damaged', 'Product', 'Seller', 'Quantity', 'Entry Price', 'Total Loss'])
    
    damaged_goods = DamagedGoods.objects.all()
    for item in damaged_goods:
        total_loss = item.quantity * item.product.entry_price
        writer.writerow([
            item.date_damaged.strftime('%Y-%m-%d'),
            item.product.name,
            item.seller.username,
            item.quantity,
            item.product.entry_price,
            total_loss
        ])
    return response





@login_required
def export_report_pdf(request):
    """ Generate a PDF report summarizing sales, expenses, and damaged goods """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="business_report.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, 750, "Business Report")
    
    y = 720
    p.setFont("Helvetica", 12)
    
    # Sales Summary
    p.drawString(50, y, "Sales Report")
    sales = Sale.objects.all()
    y -= 20
    for sale in sales[:10]:  # Show first 10 for brevity
        p.drawString(50, y, f"{sale.sale_date.strftime('%Y-%m-%d')} - {sale.customer_name} - {sale.grand_total}")
        y -= 20
    
    # Expenses Summary
    p.drawString(50, y, "Expenses Report")
    expenses = Expense.objects.all()
    y -= 20
    for expense in expenses[:10]:
        p.drawString(50, y, f"{expense.date_recorded.strftime('%Y-%m-%d')} - {expense.description} - {expense.amount}")
        y -= 20
    
    # Damaged Goods Summary
    p.drawString(50, y, "Damaged Goods Report")
    damaged_goods = DamagedGoods.objects.all()
    y -= 20
    for item in damaged_goods[:10]:
        p.drawString(50, y, f"{item.date_damaged.strftime('%Y-%m-%d')} - {item.product.name} - {item.quantity} - Loss: {item.quantity * item.product.entry_price}")
        y -= 20
    
    p.showPage()
    p.save()
    return response
