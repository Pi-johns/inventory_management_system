from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Sale, SaleItem
from inventory.models import Product
from sellers.models import Seller  
from decimal import Decimal  
from django.db.models import Sum, Q, F
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from sellers.models import Seller  # Import Seller model
from shops.models import Shop  # Import Shop model
from .models import CustomUser  # Adjust app name if needed
from .models import DamagedGoods
import csv
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import DamagedGoods
from django.utils import timezone
from sales.models import Sale, SaleItem, DamagedGoods, CreditTransaction, CashTransaction

logger = logging.getLogger(__name__)  # Setup logging


@login_required
def sales_list(request):
    """View sales based on user role with filters"""

    # Get filters from request
    date_filter = request.GET.get("date")
    shop_filter = request.GET.get("shop")
    seller_filter = request.GET.get("seller")
    payment_status_filter = request.GET.get("payment_status")
    query = request.GET.get("q")

    # Check if user is a Manager
    is_manager = request.user.groups.filter(name="Manager").exists()

    # Superadmins & Managers: See all sales + apply filters
    if request.user.is_superuser or is_manager:
        sales = Sale.objects.all()

        if date_filter:
            sales = sales.filter(sale_date__date=date_filter)

        if shop_filter:
            sales = sales.filter(shop_id=shop_filter)

        if seller_filter:
            sales = sales.filter(seller_id=seller_filter)

        if payment_status_filter:
            sales = sales.filter(payment_status=payment_status_filter)

        filters = {
            "date_filter": True,
            "shop_filter": True,
            "seller_filter": True,
            "payment_status_filter": True,
            "search_filter": True,
        }

    else:
        # Sellers: Only see their own sales + filter by date or search by customer name
        sales = Sale.objects.filter(seller=request.user)

        if date_filter:
            sales = sales.filter(sale_date__date=date_filter)

        if payment_status_filter:
            sales = sales.filter(payment_status=payment_status_filter)

        filters = {
            "date_filter": True,
            "shop_filter": False,
            "seller_filter": False,
            "payment_status_filter": True,
            "search_filter": True,
        }

    # Search by customer name (for all users)
    if query:
        sales = sales.filter(customer_name__icontains=query)

    # Sort by latest sales first
    sales = sales.order_by("-sale_date")

    # 🔹 **Sales Summary Calculations**
    total_sales_count = sales.count()
    total_sales_amount = sales.aggregate(total=Sum("grand_total"))["total"] or 0
    total_cash_sales = sales.filter(payment_status="paid").aggregate(total=Sum("grand_total"))["total"] or 0
    total_credit_sales = sales.filter(payment_status="credit").aggregate(total=Sum("grand_total"))["total"] or 0

    # **Profit Calculations**
    total_cash_profit = 0
    total_partial_profit = 0
    total_credit_unrealized_profit = 0

    for sale in sales:
        sale_items = SaleItem.objects.filter(sale=sale)

        for item in sale_items:
            product_profit = (item.price - item.product.entry_price) * item.quantity

            if sale.payment_status == "paid":
                total_cash_profit += product_profit

            elif sale.payment_status == "partial":
                paid_ratio = sale.amount_paid / sale.grand_total
                total_partial_profit += product_profit * paid_ratio
                total_credit_unrealized_profit += product_profit * (1 - paid_ratio)  # Remaining credit part

            elif sale.payment_status == "credit":
                total_credit_unrealized_profit += product_profit  # Full profit remains unrealized

    # **Net Profit Calculation**
    net_profit = total_cash_profit + total_partial_profit

    return render(request, "sales/sales.html", {
        "sales": sales,
        "filters": filters,
        "is_manager": is_manager,
        # 🔹 **Sales Summary Data**
        "total_sales_count": total_sales_count,
        "total_sales_amount": total_sales_amount,
        "total_cash_sales": total_cash_sales,
        "total_credit_sales": total_credit_sales,
        # 🔥 **Profit Data**
        "total_cash_profit": total_cash_profit,
        "total_partial_profit": total_partial_profit,
        "total_credit_unrealized_profit": total_credit_unrealized_profit,
        "net_profit": net_profit,
    })
@login_required
def delete_sale(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Allow only authorized users
    if not (request.user == sale.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to delete this sale.")
        return redirect("sales:sales_list")

    print(f"[DEBUG] Deleting Sale {sale_id} and returning items to stock")

    with transaction.atomic():
        sale_items = SaleItem.objects.filter(sale=sale)

        # **Step 1: Return Items to Stock**
        for item in sale_items:
            product = item.product
            product.stock_quantity = (product.stock_quantity or 0) + item.quantity
            product.save()
            print(f"[DEBUG] Returned {item.quantity} of {product.name} to stock.")

        # **Step 2: Delete Sale Items & Sale**
        sale_items.delete()
        sale.delete()

    messages.success(request, "Sale deleted and items returned to stock successfully.")
    return redirect("sales:sales_list")




@login_required
def manager_record_sale(request):
    user = request.user  
    print(f"🔍 DEBUG - User: {user}")

    # Ensure user is a Manager or Superadmin
    if not user.groups.filter(name__in=['Manager', 'Superadmin']).exists():
        messages.error(request, "Access Denied: Only Managers and Superadmins can record sales.")
        print(f"❌ DEBUG - Unauthorized Access: User {user} attempted to access Manager's Record Sale view.")
        return redirect('dashboard')

    # Fetch global products, shops, and sellers for the dropdown (if needed)
    products = Product.objects.all()
    shops = Shop.objects.all()
    sellers = Seller.objects.all()

    if request.method == 'POST':
        print("🔹 DEBUG - Processing Sale Submission...")
        print(f"🔍 DEBUG - Full POST Data: {request.POST}")

        # Instead of separate shop and seller fields, expect a merged field
        merged_value = request.POST.get('seller_and_shop')
        if not merged_value:
            messages.error(request, "Please select a seller and shop.")
            print("❌ DEBUG - No seller/shop selected.")
            return redirect('sales:manager_record_sale')

        try:
            seller_id, shop_id = merged_value.split('|')
            seller = Seller.objects.get(id=seller_id)
            shop = Shop.objects.get(id=shop_id)
            print(f"✅ DEBUG - Selected Seller: {seller.user.username}, Shop: {shop.name}")
        except Exception as e:
            messages.error(request, "Invalid seller/shop selection.")
            print(f"❌ DEBUG - Error parsing seller/shop: {e}")
            return redirect('sales:manager_record_sale')

        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price_per_piece[]')
        amount_paid = request.POST.get('amount_paid', '0').strip()

        # Validate and convert amount paid
        try:
            amount_paid = Decimal(amount_paid) if amount_paid else Decimal("0.00")
            print(f"✅ DEBUG - Amount Paid: {amount_paid}")
        except ValueError:
            messages.error(request, "Invalid amount paid. Please enter a valid number.")
            print(f"❌ DEBUG - Invalid amount_paid value: {amount_paid}")
            return redirect('sales:manager_record_sale')

        if not product_ids or not quantities:
            messages.error(request, "Please select at least one product.")
            print("❌ DEBUG - No products selected.")
            return redirect('sales:manager_record_sale')

        print(f"✅ DEBUG - Selected Products: {product_ids}")

        try:
            with transaction.atomic():
                print("✅ DEBUG - Creating Sale Entry...")

                sale = Sale.objects.create(
                    seller=seller.user,  # Record the sale under the selected seller's user account
                    shop=shop,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    amount_paid=amount_paid,
                    grand_total=Decimal(0),
                    balance=Decimal(0),
                    payment_status="pending"
                )
                print(f"✅ DEBUG - Sale Created: ID {sale.id}")

                grand_total = Decimal("0.00")
                print("✅ DEBUG - Processing Sale Items...")

                for product_id, quantity, price in zip(product_ids, quantities, prices):
                    product = get_object_or_404(Product, id=product_id)
                    try:
                        quantity = int(quantity)
                        price = Decimal(price)
                    except Exception as conv_err:
                        messages.error(request, "Invalid quantity or price format.")
                        print(f"❌ DEBUG - Conversion error for product ID {product_id}: {conv_err}")
                        return redirect('sales:manager_record_sale')

                    total_price = quantity * price

                    if product.stock_quantity < quantity:
                        messages.error(request, f"Not enough stock for {product.name}. Available: {product.stock_quantity}")
                        print(f"❌ DEBUG - Not enough stock for {product.name}. Available: {product.stock_quantity}")
                        return redirect('sales:manager_record_sale')

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        price=price
                    )

                    product.stock_quantity -= quantity
                    product.save()
                    print(f"✅ DEBUG - Product Sold: {product.name} | Quantity: {quantity} | Stock Left: {product.stock_quantity}")
                    grand_total += total_price

                sale.grand_total = grand_total
                sale.balance = sale.grand_total - amount_paid

                if sale.balance == Decimal(0):
                    sale.payment_status = "paid"
                elif amount_paid > Decimal(0):
                    sale.payment_status = "partial"
                else:
                    sale.payment_status = "credit"

                sale.save()
                print(f"✅ DEBUG - Final Sale Data: Grand Total: {sale.grand_total} | Balance: {sale.balance} | Payment Status: {sale.payment_status}")

                messages.success(request, "Sale recorded successfully!")
                print("✅ DEBUG - Sale Completed Successfully!")
                return redirect('sales:sales_list')

        except Exception as e:
            messages.error(request, f"Error: {e}")
            print(f"❌ DEBUG - Exception occurred: {str(e)}")
            return redirect('sales:manager_record_sale')

    return render(request, 'sales/record_sale.html', {'products': products, 'shops': shops, 'sellers': sellers})



@login_required
def credit_sales_view(request):
    """View for listing credit sales with role-based filtering."""
    
    user = request.user  # Get logged-in user
    print("DEBUG - Logged in User:", user)
    print("DEBUG - User Role:", "Superadmin" if user.is_superuser else user.role)

    try:
        # Fetch credit sales based on role
        if user.is_superuser or user.role == "manager":
            # Superadmins & Managers: See all credit and partial sales
            credit_sales = Sale.objects.filter(payment_status__in=["credit", "partial"])
            print("DEBUG - Admin/Manager Access: Viewing all credit sales")
        else:
            # Sellers: See only their own credit sales
            credit_sales = Sale.objects.filter(seller=user, payment_status__in=["credit", "partial"])
            print("DEBUG - Seller Access: Viewing own credit sales only")

        print("DEBUG - Total Credit Sales Fetched:", credit_sales.count())

        # Filtering
        search_query = request.GET.get("q")
        seller_filter = request.GET.get("seller")
        shop_filter = request.GET.get("shop")
        date_filter = request.GET.get("date")

        if search_query:
            credit_sales = credit_sales.filter(customer_name__icontains=search_query)
            print("DEBUG - Filter Applied: Search Query =", search_query)

        if seller_filter and (user.is_superuser or user.role == "manager"):
            credit_sales = credit_sales.filter(seller__id=seller_filter)
            print("DEBUG - Filter Applied: Seller =", seller_filter)

        if shop_filter and (user.is_superuser or user.role == "manager"):
            credit_sales = credit_sales.filter(shop__id=shop_filter)
            print("DEBUG - Filter Applied: Shop =", shop_filter)

        if date_filter:
            credit_sales = credit_sales.filter(sale_date__date=date_filter)
            print("DEBUG - Filter Applied: Date =", date_filter)

        # ✅ Total Credit Sales Amount (Sum of all credit and partial sales)
        total_credit_sales_amount = credit_sales.aggregate(total=Sum('grand_total'))['total'] or 0
        print("DEBUG - Total Credit Sales Amount:", total_credit_sales_amount)

        # ✅ Total Amount Paid from Partial Payments
        total_partial_payments = credit_sales.filter(payment_status="partial").aggregate(total=Sum('amount_paid'))['total'] or 0
        print("DEBUG - Total Partial Payments:", total_partial_payments)

        # ✅ Remaining Balance from Partial Payments (Credit Balance)
        total_partial_balance = total_credit_sales_amount - total_partial_payments
        print("DEBUG - Remaining Partial Sales Balance:", total_partial_balance)

        # ✅ Total Credit Balance (Total Credit Sales Amount + Remaining Partial Sales Balance)
        total_credit_balance = total_partial_balance
        print("DEBUG - Total Credit Balance:", total_credit_balance)

        # ✅ Total Credit Sales Count (Including Partial Payments)
        total_credit_sales = credit_sales.count()
        print("DEBUG - Total Credit Sales Count:", total_credit_sales)

        # ✅ Total Partial Payments Count
        total_partial_sales = credit_sales.filter(payment_status="partial").count()
        print("DEBUG - Total Partial Sales Count:", total_partial_sales)

        context = {
            "credit_sales": credit_sales,
            "total_credit_sales_amount": total_credit_sales_amount,
            "total_credit_balance": total_credit_balance,
            "total_credit_sales": total_credit_sales,
            "total_partial_sales": total_partial_sales,
            "total_partial_payments": total_partial_payments,
        }
        return render(request, "sales/credit_sales.html", context)

    except Exception as e:
        print("ERROR - Failed to fetch credit sales:", str(e))
        return render(request, "sales/credit_sales.html", {"error": "An error occurred while fetching credit sales."})

# 1. Mark Sale as Paid

@login_required
def mark_sale_as_paid(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Ensure user has permission (Seller can mark their own, Manager/Admin can mark any)
    if not (request.user == sale.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to mark this sale as paid.")
        print(f"❌ DEBUG - Unauthorized Access: User {request.user} attempted to mark Sale {sale_id} as paid.")
        return redirect("sales:sales_list")

    print(f"✅ DEBUG - Marking Sale {sale_id} as Paid")

    with transaction.atomic():
        # Ensure correct field usage
        sale.amount_paid = sale.grand_total  # Set amount paid to grand total
        sale.balance = Decimal(0)  # No balance remaining
        sale.payment_status = "paid"
        sale.save()

    print(f"✅ DEBUG - Sale {sale_id} Updated: amount_paid={sale.amount_paid}, payment_status={sale.payment_status}, balance={sale.balance}")
    messages.success(request, "Sale marked as paid successfully.")

    return redirect("sales:sales_list")

# 2. Return Sale as Damaged

@login_required
def return_sale_as_damaged(request, sale_id):
    """Marks an entire sale as damaged and removes it without restocking."""
    
    sale = get_object_or_404(Sale, id=sale_id)

    # Allow only the seller, managers, or admins
    if not (request.user == sale.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to mark this sale as damaged.")
        return redirect("sales:sales_list")

    print(f"[DEBUG] Returning Sale {sale_id} as Damaged")

    with transaction.atomic():
        sale_items = SaleItem.objects.filter(sale=sale)

        # ✅ Step 1: Move Items to Damaged Goods (DO NOT RESTOCK)
        for item in sale_items:
            print(f"[DEBUG] Logging {item.product.name} as damaged, Qty: {item.quantity}")
            DamagedGoods.objects.create(
                product=item.product,
                seller=sale.seller,  # Track responsible seller
                quantity=item.quantity,
                date_damaged=timezone.now()
            )

        # ✅ Step 2: Adjust Financial Records (Fixing the DeferredAttribute Error)
        total_amount_paid = sale.amount_paid or 0  # Ensure it's a valid number
        total_credit = sale.grand_total - total_amount_paid  # Corrected calculation

        # Deducting paid amount from cash transactions
        if total_amount_paid > 0:
            print(f"[DEBUG] Deducting {total_amount_paid} from cash balance")
            CashTransaction.objects.create(
                sale=sale,
                amount_paid=-total_amount_paid,  # Correct field name
                recorded_by=request.user,  # Track the user performing the transaction
            )

        # Deducting remaining balance from credit transactions
        if total_credit > 0:
            print(f"[DEBUG] Deducting {total_credit} from credit balance")
            CreditTransaction.objects.create(
                sale=sale,
                amount_paid=-total_credit,  # Correct field name
                recorded_by=request.user,  # Track the user performing the transaction
            )
            

        # ✅ Step 3: Remove Sale & Sale Items (WITHOUT Restocking)
        print(f"[DEBUG] Removing Sale {sale_id} from records")
        sale_items.delete()  # Delete sale items
        sale.delete()  # Delete the sale itself

    messages.success(request, "Sale marked as damaged and removed successfully.")
    return redirect("sales:sales_list")
# 3. Return Sale to Stock

@login_required
def return_sale_to_stock(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Allow only the seller or managers/admins to perform this action
    if not (request.user == sale.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to return this sale to stock.")
        return redirect("sales:sales_list")

    print(f"[DEBUG] Returning Sale {sale_id} to Stock")

    with transaction.atomic():
        sale_items = SaleItem.objects.filter(sale=sale)
        for item in sale_items:
            print(f"[DEBUG] Restoring {item.product.name} to stock, Qty: {item.quantity}")

            # Ensure stock is initialized before updating
            if item.product.stock_quantity is None:
                item.product.stock_quantity = 0  # Prevent NoneType error

            item.product.stock_quantity += item.quantity  # ✅ Increase stock
            item.product.save()

            print(f"[DEBUG] Updated Stock: {item.product.name} - New Qty: {item.product.stock_quantity}")

            # Now delete the item from SaleItem (not moving to DamagedGoods)
            item.delete()
            print(f"[DEBUG] SaleItem {item.id} deleted.")

        # After all items are returned to stock, delete the sale record itself
        sale.delete()
        print(f"[DEBUG] Sale {sale_id} deleted.")

    messages.success(request, "Sale returned to stock successfully.")
    return redirect("sales:sales_list")  # Redirect to the sales list
# 4. Mark Item as Damaged

@login_required
def mark_item_as_damaged(request, item_id):
    item = get_object_or_404(SaleItem, id=item_id)
    sale = item.sale  # Get the related sale

    # Allow only the seller, managers, or admins
    if not (request.user == sale.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to mark this item as damaged.")
        return redirect("sales:edit_sale", sale_id=sale.id)

    print(f"[DEBUG] Marking Item {item_id} as Damaged")
    print(f"[DEBUG] Product: {item.product.name}, Quantity: {item.quantity}, Sale ID: {sale.id}")

    with transaction.atomic():
        # **Step 1: Move Item to DamagedGoods**
        DamagedGoods.objects.create(
            product=item.product,
            seller=sale.seller,
            quantity=item.quantity,
            date_damaged=timezone.now()
        )
        print(f"[DEBUG] Item moved to DamagedGoods successfully.")

        # **Step 2: Adjust Sale Amounts**
        item_total_price = item.unit_price * item.quantity  # Total price of damaged item
        print(f"[DEBUG] Deducting {item_total_price} from sale total.")

        # Ensure that amount_paid does not go negative
        amount_refunded = min(item_total_price, sale.amount_paid)

        # Update the sale totals
        sale.total_price = max(0, sale.total_price - item_total_price)
        sale.amount_paid -= amount_refunded  # Reduce paid amount but not below zero
        sale.save()

        # **Step 3: Adjust Cash or Credit Balance**
        if amount_refunded > 0:
            print(f"[DEBUG] Deducting {amount_refunded} from cash balance")
            CashTransaction.objects.create(
                sale=sale,
                amount_paid=-amount_refunded,  # Correct field name
                recorded_by=request.user,
            )

        # Remaining credit balance to be adjusted
        remaining_credit_adjustment = item_total_price - amount_refunded
        if remaining_credit_adjustment > 0:
            print(f"[DEBUG] Deducting {remaining_credit_adjustment} from credit balance")
            CreditTransaction.objects.create(
                sale=sale,
                amount_paid=-remaining_credit_adjustment,  # Correct field name
                recorded_by=request.user,
            )

        # **Step 4: Remove from SaleItem**
        item.delete()
        print(f"[DEBUG] Item removed from SaleItem.")

        # **Step 5: Check if Sale Has Remaining Items**
        remaining_items = SaleItem.objects.filter(sale=sale).exists()

        if not remaining_items:
            # If no items left, mark sale as canceled (since it no longer exists)
            sale.status = "Canceled"  # Ensure this field exists in Sale model
            sale.save()
            print(f"[DEBUG] Sale {sale.id} marked as 'Canceled' (No remaining items).")

    messages.success(request, "Item marked as damaged successfully.")
    return redirect("sales:edit_sale", sale_id=sale.id)


@login_required
def mark_item_as_returned_to_stock(request, item_id):
    item = get_object_or_404(SaleItem, id=item_id)

    # Allow only the seller or managers/admins to perform this action
    if not (request.user == item.sale.seller or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to return this item to stock.")
        return redirect("sales:edit_sale", sale_id=item.sale.id)

    print(f"[DEBUG] Returning Item {item_id} to Stock - {item.product.name}, Qty: {item.quantity}")

    with transaction.atomic():
        # Ensure stock_quantity is initialized
        if item.product.stock_quantity is None:
            item.product.stock_quantity = 0  # Prevent NoneType error
        
        # Update stock quantity and save
        item.product.stock_quantity += item.quantity
        item.product.save()
        print(f"[DEBUG] Updated Stock: {item.product.name} - New Qty: {item.product.stock_quantity}")

        # Delete SaleItem after updating stock
        item.delete()
        print(f"[DEBUG] SaleItem {item_id} deleted.")

    messages.success(request, "Item returned to stock successfully.")
    return redirect("sales:edit_sale", sale_id=item.sale.id)

# Configure logging
logger = logging.getLogger(__name__)

@login_required
def damaged_goods_list(request):
    """ View to list all damaged goods with additional context """
    logger.info("Fetching damaged goods from database...")
    damaged_goods = DamagedGoods.objects.select_related('product', 'seller').order_by('-date_damaged')
    
    total_damaged = damaged_goods.count()
    logger.info(f"Total damaged count: {total_damaged}")

    # Initialize total loss values
    total_loss = Decimal(0)
    total_loss_count = 0  # Number of lost items

    # Calculate total loss and count total lost items
    for item in damaged_goods:
        if item.product.entry_price:
            item_loss = item.product.entry_price * item.quantity
            total_loss += item_loss
            total_loss_count += item.quantity  # Count the number of lost items
            logger.debug(f"Product: {item.product.name}, Quantity Lost: {item.quantity}, Loss: ${item_loss:.2f}")
    
    logger.info(f"Total loss calculated: ${total_loss:.2f}")
    logger.info(f"Total number of lost items: {total_loss_count}")

    context = {
        'damaged_goods': damaged_goods,
        'total_damaged': total_damaged,
        'total_loss': total_loss,  # Total monetary loss
        'total_loss_count': total_loss_count,  # Total number of items lost
        'today': timezone.now().date(),  # Ensure timezone-aware date
    }
    logger.info("Rendering template with context data.")
    return render(request, 'sales/damaged.html', context)

def export_damaged_goods_csv(request):
    """Export damaged goods as CSV"""
    logger.info("Generating CSV file for damaged goods...")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="damaged_goods.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Product', 'Seller', 'Date Damaged', 'Quantity', 'Entry Price', 'Total Loss'])
    
    damaged_goods = DamagedGoods.objects.select_related('product', 'seller')
    logger.info(f"Exporting {damaged_goods.count()} damaged items to CSV.")
    
    for item in damaged_goods:
        total_loss = item.quantity * item.product.entry_price if item.product.entry_price else 0
        writer.writerow([
            item.product.name,
            item.seller.username,
            item.date_damaged.strftime('%Y-%m-%d %H:%M:%S'),
            item.quantity,
            item.product.entry_price,
            total_loss
        ])
        logger.debug(f"Exported: {item.product.name}, Loss: ${total_loss:.2f}")
    
    logger.info("CSV export completed successfully.")
    return response

def export_damaged_goods_pdf(request):
    """Export damaged goods as PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="damaged_goods.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y_position = height - 40
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, y_position, "Damaged Goods Report")
    y_position -= 30
    
    p.setFont("Helvetica-Bold", 12)
    columns = ['Product', 'Seller', 'Date', 'Qty', 'Entry Price', 'Total Loss']
    x_positions = [40, 140, 240, 300, 350, 430]
    
    for i, column in enumerate(columns):
        p.drawString(x_positions[i], y_position, column)
    y_position -= 20
    
    p.setFont("Helvetica", 10)
    damaged_goods = DamagedGoods.objects.select_related('product', 'seller')
    for item in damaged_goods:
        if y_position < 50:
            p.showPage()
            y_position = height - 40
        
        p.drawString(x_positions[0], y_position, item.product.name)
        p.drawString(x_positions[1], y_position, item.seller.username)
        p.drawString(x_positions[2], y_position, item.date_damaged.strftime('%Y-%m-%d'))
        p.drawString(x_positions[3], y_position, str(item.quantity))
        p.drawString(x_positions[4], y_position, str(item.product.entry_price))
        p.drawString(x_positions[5], y_position, str(item.quantity * item.product.entry_price))
        
        y_position -= 20
    
    p.showPage()
    p.save()
    return response





def top_performing_shops(request):
    """Retrieve the top 4 shops based on total sales (cash + credit)"""
    top_shops = (
        Shop.objects.annotate(
            total_cash_sales=Sum("sale__grand_total", filter=Q(sale__payment_status="paid")),
            total_credit_sales=Sum("sale__grand_total", filter=Q(sale__payment_status="credit")),
            total_sales=Sum("sale__grand_total"),
        )
        .order_by("-total_sales")[:4]  # Rank by total sales, top 4
    )

    return render(request, "dashboard/manager_dashboard.html", {"top_shops": top_shops})


def low_stock_items_dashboard(request):
    """Retrieve first 4 low-stock products for dashboard"""
    low_stock_items = Product.objects.filter(stock_quantity__lt=F("threshold")).order_by("stock_quantity")[:4]

    return render(request, "dashboard/manager_dashboard.html", {"low_stock_items": low_stock_items})


def all_low_stock_items(request):
    """Retrieve all low-stock products for detailed listing"""
    low_stock_items = Product.objects.filter(stock_quantity__lt=F("threshold")).order_by("stock_quantity")

    return render(request, "inventory/low_stock_list.html", {"low_stock_items": low_stock_items})





@login_required
def mark_stock_as_damaged(request):
    """View for managers and super admins to mark stock items as damaged."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to mark stock as damaged.")
        return redirect("inventory:stock_list")

    if request.method == "POST":
        product_id = request.POST.get("product")  # ✅ Changed from stock_item to product
        damaged_quantity = int(request.POST.get("damaged_quantity", 0))

        product = get_object_or_404(Product, id=product_id)  # ✅ Get product directly

        if damaged_quantity < 1 or damaged_quantity > product.stock_quantity:
            messages.error(request, "Invalid quantity selected.")
            return redirect("inventory:mark_stock_as_damaged")

        with transaction.atomic():
            # Move item to DamagedGoods
            DamagedGoods.objects.create(
                product=product,
                seller=request.user,  # Manager who marks it as damaged
                quantity=damaged_quantity,
                date_damaged=timezone.now(),
            )

            # Reduce product stock
            product.stock_quantity -= damaged_quantity

            # Ensure no negative stock
            if product.stock_quantity < 0:
                product.stock_quantity = 0

            product.save()  # ✅ Save the updated stock

        messages.success(request, "Stock item successfully marked as damaged.")
        return redirect("sales:damaged_goods_list")

    # Get available products for dropdown selection
    products = Product.objects.filter(stock_quantity__gt=0)  # ✅ Fetch products with stock
    return render(request, "sales/enter_damaged.html", {"products": products})