from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Seller
from sales.models import Payment, Sale, SaleItem
from .forms import SellerForm 
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.contrib import messages
from django.db import transaction
from inventory.models import Product
from sellers.models import Seller  
from decimal import Decimal  
from django.db.models import Sum, Q, F
import logging
from sellers.models import Seller  # Import Seller model
from shops.models import Shop


logger = logging.getLogger(__name__)  # Setup logging

CustomUser = get_user_model()  # Get the custom user model


def is_manager_or_superadmin(user):
    """Helper function to check if the user is a Manager or Superadmin."""
    return user.role in ["manager", "superadmin"]

@login_required
def seller_list(request):
    """Displays a list of all sellers. Accessible by Superadmin & Manager."""
    if not is_manager_or_superadmin(request.user):
        return render(request, "base/403.html")

    sellers = Seller.objects.select_related("user", "shop").all()
    return render(request, "dashboard/sellers.html", {"sellers": sellers})

def create_seller(request):
    if request.method == "POST":
        form = SellerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']  # Phone is for Seller, not User
            shop = form.cleaned_data['shop']
            password = form.cleaned_data['password']

            # Create User (DO NOT pass phone here)
            user = CustomUser.objects.create_user(username=username, email=email, password=password)

            # Create Seller (Assign phone number here)
            seller = Seller.objects.create(user=user, phone=phone, shop=shop)

            return redirect('sellers:seller_list')
    else:
        form = SellerForm()
    
    return render(request, 'dashboard/create_seller.html', {'form': form})

@login_required
def edit_seller(request, seller_id):
    """Allows a Superadmin or Manager to edit a seller."""
    if not is_manager_or_superadmin(request.user):
        return render(request, "base/403.html")

    seller = get_object_or_404(Seller, id=seller_id)

    if request.method == "POST":
        form = SellerForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, "Seller updated successfully!")
            return redirect("sellers:seller_list")

    else:
        form = SellerForm(instance=seller)

    return render(request, "dashboard/edit_seller.html", {"form": form, "seller": seller})

@login_required
def delete_seller(request, seller_id):
    """Allows a Superadmin or Manager to delete a seller."""
    if not is_manager_or_superadmin(request.user):
        return render(request, "base/403.html")

    seller = get_object_or_404(Seller, id=seller_id)
    seller.user.delete()  # Delete the associated user
    seller.delete()
    messages.success(request, "Seller deleted successfully!")
    return redirect("sellers:seller_list")

@login_required
def seller_dashboard(request):
    """Dashboard view for sellers to see their sales and earnings."""
    
    # Ensure the logged-in user is a Seller
    user = request.user
    seller = get_object_or_404(Seller, user=request.user)

    print("DEBUG - Logged-in User:", request.user, type(request.user))
    print("DEBUG - Seller Object:", seller, type(seller))
    


    # Get all sales where seller is the logged-in user
    total_sales = Sale.objects.filter(seller=seller.user).count()
    
    # Define today's date
    today = now().date()
    
    # Fetch today's sales
    recent_sales = Sale.objects.filter(seller=seller.user, sale_date__date=today)

    # Get all unpaid credit sales (NEW FILTER)
    credit_sales = Sale.objects.filter(seller=user, payment_status__in=["credit", "partial"])
    print("DEBUG - Seller Access: Viewing own credit sales only")    
    total_credit_balance = credit_sales.aggregate(total=Sum('grand_total') - Sum('amount_paid'))['total'] or 0
    print("DEBUG - Total Credit Balance Remaining:", total_credit_balance)
    # Debugging Logs
    print("DEBUG - Total Sales:", total_sales)
    print("DEBUG - Credit Sales Count:", credit_sales.count())
    print("DEBUG - Total Credit Amount:", total_credit_balance)

    context = {
        'total_sales': total_sales,
        'credit_sales': credit_sales,
        'total_credit': total_credit_balance,
        'recent_sales': recent_sales
    }
    return render(request, 'dashboard/seller_dashboard.html', context)


@login_required
def make_payment(request, sale_id):
    """Process partial or full payments for a credit sale."""

    sale = get_object_or_404(Sale, id=sale_id, seller=request.user)

    if request.method == "POST":
        amount_paid = float(request.POST.get("amount_paid", 0))

        if amount_paid > 0:
            # Record payment
            Payment.objects.create(sale=sale, amount=amount_paid)

            # Update payment status
            sale.update_payment_status()
            if sale.is_credit:
                sale.credit_sale.update_credit_status()

            # If fully paid, remove from credit sales list
            if sale.is_paid:
                sale.credit_sale.paid = True
                sale.credit_sale.save()

        return redirect("credit_sales_list")  # Redirect back to the list

    context = {"sale": sale}
    return render(request, "dashboard/make_payment.html", context)







@login_required
def seller_create_sale(request):
    user = request.user
    print(f"🔍 DEBUG - User: {user}")

    # Check if user is a seller
    try:
        seller = Seller.objects.get(user=user)
        print(f"✅ DEBUG - Seller Found: {seller}")
    except Seller.DoesNotExist:
        messages.error(request, "You do not have permission to record sales.")
        logger.warning("❌ DEBUG - User %s is not a seller.", user)
        print(f"❌ DEBUG - User {user} is not a seller.")
        return redirect('sales:sales_list')

    # Get assigned shop
    shop = seller.shop
    if not shop:
        messages.error(request, "You must be assigned to a shop before making a sale.")
        logger.warning("❌ DEBUG - Seller %s has no assigned shop.", seller)
        print(f"❌ DEBUG - Seller {seller} has no assigned shop.")
        return redirect('sales:sales_list')

    print(f"✅ DEBUG - Seller's Assigned Shop: {shop.name}")

    # Get products available in the assigned shop
    products = Product.objects.all()

    if request.method == 'POST':
        print(f"🔹 DEBUG - Processing Sale Submission...")
        print(f"🔍 DEBUG - Full POST Data: {request.POST}")

        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price_per_piece[]')
        amount_paid = request.POST.get('amount_paid', '0').strip()

        try:
            amount_paid = Decimal(amount_paid) if amount_paid else Decimal("0.00")
        except ValueError:
            messages.error(request, "Invalid amount paid. Please enter a valid number.")
            print(f"❌ DEBUG - Invalid amount_paid value: {request.POST.get('amount_paid')}")
            return redirect('sellers:sellers_record_sale')

        if not product_ids or not quantities:
            messages.error(request, "Please select at least one product.")
            print("❌ DEBUG - No products selected.")
            return redirect('sellers:sellers_record_sale')

        print(f"✅ DEBUG - Selected Products: {product_ids}")

        # Stock validation
        for product_id, quantity in zip(product_ids, quantities):
            try:
                product = Product.objects.get(id=product_id)
                if product.stock_quantity < int(quantity):
                    messages.error(request, f"Not enough stock for {product.name}. Available: {product.stock_quantity}")
                    print(f"❌ DEBUG - Not enough stock for {product.name}. Available: {product.stock_quantity}")
                    return redirect('sellers:sellers_record_sale')
            except Product.DoesNotExist:
                messages.error(request, "One or more selected products do not exist.")
                print(f"❌ DEBUG - Product with ID {product_id} does not exist in shop {shop.name}.")
                return redirect('sellers:sellers_record_sale')

        try:
            with transaction.atomic():
                print("✅ DEBUG - Creating Sale Entry...")

                sale = Sale.objects.create(
                    seller=user,  
                    shop=shop,  
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    amount_paid=amount_paid,
                    grand_total=Decimal(0),
                    balance=Decimal(0),
                    payment_status="pending"
                )
                sale.save()  # ✅ Save first to get a primary key
                sale.update_totals()  # ✅ Now call update_totals()
                sale.save() 

                print(f"✅ DEBUG - Sale Created: ID {sale.id}")

                grand_total = Decimal("0.00")

                print("✅ DEBUG - Processing Sale Items...")

                for product_id, quantity, price in zip(product_ids, quantities, prices):
                    product = Product.objects.get(id=product_id)
                    quantity = int(quantity)
                    price = Decimal(price)
                    total_price = Decimal(quantity) * price

                    print(f"✅ DEBUG - Adding SaleItem: Product {product.name} | Quantity {quantity} | Price {price}")

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
            return redirect('sales:seller_create_sale')

    return render(request, 'sales/record_sale.html', {'products': products, 'shop': shop})

@login_required
def edit_sale(request, sale_id):
    user = request.user  
    sale = get_object_or_404(Sale, id=sale_id)

    sale_items = list(SaleItem.objects.filter(sale=sale).select_related("product"))
    print(f"\n[DEBUG] Editing Sale ID: {sale_id}")
    print(f"[DEBUG] Sale Items Count: {len(sale_items)}")

    for item in sale_items:
        print(f"[DEBUG] SaleItem - Product: {item.product.name}, ID: {item.product.id}, Qty: {item.quantity}, Price: {item.price}, Total: {item.total_price}")

    # Authorization Check
    if user != sale.seller and not user.is_superuser and not user.groups.filter(name__in=['Manager']).exists():
        messages.error(request, "You are not allowed to edit this sale.")
        return redirect("sales:sales_list")

    if request.method == "POST":
        print("[DEBUG] Processing Sale Edit...")

        product_ids = request.POST.getlist("product[]")
        quantities = request.POST.getlist("quantity[]")
        price_list = request.POST.getlist("price_per_piece[]")  
        amount_paid_raw = request.POST.get("amount_paid", "0").strip()
        customer_name = request.POST.get("customer_name")
        customer_phone = request.POST.get("customer_phone")

        if user.is_superuser or user.groups.filter(name__in=['Manager']).exists():
            seller_id = request.POST.get("seller")
            shop_id = request.POST.get("shop")
        else:
            seller_id = sale.seller.id  
            shop_id = sale.shop.id  

        try:
            amount_paid = Decimal(amount_paid_raw) if amount_paid_raw else Decimal("0.00")
        except ValueError:
            messages.error(request, "Invalid amount paid.")
            return redirect("sellers:edit_sale", sale_id=sale.id)

        grand_total = Decimal("0.00")

        try:
            with transaction.atomic():
                # Restore stock **before deleting items**
                for item in sale_items:
                    print(f"[DEBUG] Restoring stock for: {item.product.name}, Qty: {item.quantity}")
                    item.product.stock_quantity += item.quantity
                    item.product.save()
                
                # Now delete all sale items at once
                SaleItem.objects.filter(sale=sale).delete()

                # Process updated sale items
                for prod_id, qty_raw, price_raw in zip(product_ids, quantities, price_list):
                    if prod_id and qty_raw and price_raw:
                        product = get_object_or_404(Product, id=prod_id)
                        try:
                            quantity = int(qty_raw)
                            price = Decimal(price_raw)
                        except ValueError:
                            messages.error(request, "Invalid quantity or price format.")
                            return redirect("sales:edit_sale", sale_id=sale.id)

                        if product.stock_quantity < quantity:
                            messages.error(request, f"Not enough stock for {product.name}.")
                            return redirect("sales:edit_sale", sale_id=sale.id)

                        product.stock_quantity -= quantity
                        product.save()

                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity,
                            price=price
                        )
                        grand_total += quantity * price

                # Allow Admin/Manager to update seller/shop
                if user.is_superuser or user.groups.filter(name__in=['Manager']).exists():
                    sale.seller = get_object_or_404(CustomUser, id=seller_id)
                    sale.shop = get_object_or_404(Shop, id=shop_id)

                # Only update the necessary fields
                sale.customer_name = customer_name
                sale.customer_phone = customer_phone
                sale.amount_paid = amount_paid  # Ensure amount_paid is set
                sale.update_totals()  # This will set grand_total, balance, and status
                sale.last_edited = now()
                sale.save(update_fields=["customer_name", "customer_phone", "amount_paid", "grand_total", "balance", "payment_status", "last_edited", "seller", "shop"])

                messages.success(request, "Sale updated successfully.")
                print("[DEBUG] Sale updated successfully!")
                return redirect("sales:sales_list")

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            print(f"[ERROR] Exception during sale edit: {e}")
            return redirect("sellers:edit_sale", sale_id=sale.id)

    # Fetch necessary data for the template
    products = Product.objects.all()
    sellers = CustomUser.objects.filter(role="seller")
    shops = Shop.objects.all()

    return render(request, "sales/edit_sale.html", {
        "sale": sale,
        "sale_items": sale_items,
        "products": products,
        "sellers": sellers,
        "shops": shops,
    })
