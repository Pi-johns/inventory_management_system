from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from inventory.models import Product
from sales.models import Sale, CreditSale
from reports.models import ProfitReport
from accounts.models import Seller
from notifications.models import Notification
from django.urls import reverse
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser as User
from django.contrib import messages
from .forms import SellerForm, ManagerForm
from django.contrib.auth import get_user_model


def get_dashboard_data(user):
    """ Helper function to fetch relevant dashboard data based on user role. """
    data = {}

    # Sales Data
    sales = Sale.objects.all() if user.role in ["superadmin", "manager"] else Sale.objects.filter(seller=user)
    data["total_sales"] = sales.count()
    data["total_revenue"] = sum(sale.total_price for sale in sales)
    
    # Profit Analysis
    profits = ProfitReport.objects.all() if user.role in ["superadmin", "manager"] else ProfitReport.objects.filter(seller=user)
    data["total_profit"] = sum(profit.net_profit for profit in profits)

    # Low Stock Alert
    low_stock_products = Product.objects.filter(stock_quantity__lte=5)
    data["low_stock_count"] = low_stock_products.count()

    # Credit Sales
    credit_sales = CreditSale.objects.all() if user.role in ["superadmin", "manager"] else CreditSale.objects.filter(seller=user)
    data["credit_sales_count"] = credit_sales.count()
    
    # Notifications
    notifications = Notification.objects.all() if user.role in ["superadmin", "manager"] else Notification.objects.filter(user=user)
    data["notifications"] = notifications.order_by("-created_at")[:10]  # Show latest 10 notifications

    return data

@login_required
def superadmin_dashboard(request):
    if request.user.role != "superadmin":
        return redirect(reverse("forbidden"))  # Redirect unauthorized users

    context = get_dashboard_data(request.user)
    return render(request, "dashboard/superadmin_dashboard.html", context)

@login_required
def manager_dashboard(request):
    if request.user.role != "manager":
        return redirect(reverse("forbidden"))

    context = get_dashboard_data(request.user)
    return render(request, "dashboard/manager_dashboard.html", context)

@login_required
def seller_dashboard(request):
    if request.user.role != "seller":
        return redirect(reverse("forbidden"))

    context = get_dashboard_data(request.user)
    return render(request, "dashboard/seller_dashboard.html", context)


def forbidden_view(request):
    return render(request, "base/403.html", status=403)



@login_required
def create_seller(request):
    if request.user.role != "manager":
        return render(request, "base/403.html")

    if request.method == "POST":
        form = SellerForm(request.POST)
        if form.is_valid():
            seller = form.save(commit=False)
            seller.role = "seller"
            seller.save()
            messages.success(request, "Seller created successfully!")
            return redirect("dashboard:seller_list")
    else:
        form = SellerForm()

    return render(request, "dashboard/create_seller.html", {"form": form})

@login_required
def edit_seller(request, seller_id):
    if request.user.role != "manager":
        return render(request, "base/403.html")

    seller = get_object_or_404(User, id=seller_id, role="seller")

    if request.method == "POST":
        form = SellerForm(request.POST, instance=seller)
        if form.is_valid():
            form.save()
            messages.success(request, "Seller updated successfully!")
            return redirect("dashboard:seller_list")

    else:
        form = SellerForm(instance=seller)

    return render(request, "dashboard/edit_seller.html", {"form": form, "seller": seller})

@login_required
def delete_seller(request, seller_id):
    if request.user.role != "manager":
        return render(request, "403.html")

    seller = get_object_or_404(User, id=seller_id, role="seller")
    seller.delete()
    messages.success(request, "Seller deleted successfully!")
    return redirect("dashboard:seller_list")


def seller_list(request):
    """Displays a list of all sellers."""
    sellers = Seller.objects.select_related('user', 'shop').all()
    return render(request, "dashboard/sellers.html", {"sellers": sellers})



User = get_user_model()

# Superadmin check
def is_superadmin(user):
    return user.is_superadmin

# ✅ List all Managers
@login_required
@user_passes_test(is_superadmin)
def manager_list(request):
    managers = User.objects.filter(role="manager")  # Fetch only managers
    return render(request, "dashboard/managers.html", {"managers": managers})

# ✅ Create a Manager
@login_required
@user_passes_test(is_superadmin)
def create_manager(request):
    if request.method == "POST":
        form = ManagerForm(request.POST)
        if form.is_valid():
            manager = form.save(commit=False)
            manager.role = "manager"
            manager.set_password(form.cleaned_data["password"])  # Set hashed password
            manager.save()
            messages.success(request, "Manager created successfully!")
            return redirect("dashboard:manager_list")  # Redirect to Manager List
    else:
        form = ManagerForm()

    return render(request, "dashboard/createmanager.html", {"form": form})

# ✅ Edit Manager
@login_required
@user_passes_test(is_superadmin)
def edit_manager(request, manager_id):
    manager = get_object_or_404(User, id=manager_id, role="manager")

    if request.method == "POST":
        form = ManagerForm(request.POST, instance=manager)
        if form.is_valid():
            form.save()
            messages.success(request, "Manager updated successfully!")
            return redirect("dashboard:manager_list")  # Redirect to Manager List

    else:
        form = ManagerForm(instance=manager)

    return render(request, "dashboard/editmanager.html", {"form": form, "manager": manager})

# ✅ Delete Manager
@login_required
@user_passes_test(is_superadmin)
def delete_manager(request, manager_id):
    manager = get_object_or_404(User, id=manager_id, role="manager")
    manager.delete()
    messages.success(request, "Manager deleted successfully!")
    return redirect("dashboard:manager_list")  # Redirect to Manager List


def sales_dashboard(request):
    """Directs user to Sales Management Dashboard."""
    return render(request, 'sales/sales.html')