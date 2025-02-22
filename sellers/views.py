from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Seller
from sales.models import Payment
from .forms import SellerForm
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect


User = get_user_model()  # Get the custom user model


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
            user = User.objects.create_user(username=username, email=email, password=password)

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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from sales.models import Sale  # Import the Sale model
from django.db.models import Sum



@login_required
def seller_dashboard(request):
    """Dashboard view for sellers to see their sales and earnings."""
    
    # Check if the logged-in user is associated with a Seller account
    seller = get_object_or_404(Seller, user=request.user)

    # Ensure Sale.seller is a CustomUser instance
    total_sales = Sale.objects.filter(seller=request.user).count()
    
    # Total Revenue (Only fully paid sales)
    total_revenue = Sale.objects.filter(seller=request.user, payment_status="paid").aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    # Total Credit Sales (Unpaid sales)
    credit_sales = Sale.objects.filter(seller=request.user, payment_status="credit").aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0

    # Fetch recent sales
    recent_sales = Sale.objects.filter(seller=request.user).order_by('-date')[:5]

    # Debugging Logs
    print("DEBUG - Logged in User:", request.user)
    print("DEBUG - Seller Object:", seller)
    print("DEBUG - Total Sales:", total_sales)
    print("DEBUG - Total Revenue:", total_revenue)
    print("DEBUG - Credit Sales:", credit_sales)

    context = {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'credit_sales': credit_sales,
        'recent_sales': recent_sales
    }
    return render(request, 'dashboard/seller_dashboard.html', context)

@login_required
def credit_sales(request):
    """Display all unpaid credit sales for the logged-in seller."""
    
    # Ensure user is a seller
    try:
        seller = request.user.seller  
    except AttributeError:
        return render(request, "base/403.html", status=403)

    # Get only credit sales (unpaid) for this seller
    credit_sales = Sale.objects.filter(seller=request.user, is_credit=True)

    # Calculate total credit amount
    total_credit = credit_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'credit_sales': credit_sales,
        'total_credit': total_credit
    }
    return render(request, 'dashboard/credit_sales.html', context)


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