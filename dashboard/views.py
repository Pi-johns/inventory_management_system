from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from inventory.models import Product
from sales.models import Sale
from notifications.models import Notification
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import ManagerForm
from django.contrib.auth.models import Group
# from shop_management.dashboard.permissions import is_superadmin

def is_superadmin(user):
    return user.role == "superadmin"


User = get_user_model()


from sales.models import Sale

from inventory.models import Product
from notifications.models import Notification

def get_dashboard_data(user):
    """ Helper function to fetch relevant dashboard data based on user role. """
    data = {}

    # ✅ Sales Data (Show all sales for Superadmin & Manager)
    sales = Sale.objects.all() if user.role in ["superadmin", "manager"] else Sale.objects.filter(seller=user)
    data["total_sales"] = sales.count()
    data["total_revenue"] = sum(sale.grand_total for sale in sales)

    # ✅ Profit Analysis (Only for Superadmin & Manager)


    # ✅ Low Stock Alert (For Everyone)
    low_stock_products = Product.objects.filter(stock_quantity__lte=5)
    data["low_stock_count"] = low_stock_products.count()

    # ✅ Outstanding Payments (Credit & Partial Payments)
    outstanding_sales = sales.filter(balance__gt=0)  # Sales with unpaid balance
    data["outstanding_sales_count"] = outstanding_sales.count()
    data["outstanding_balance_total"] = sum(sale.balance for sale in outstanding_sales)

    # ✅ Notifications (Show all for Admin & Manager, only user-specific for Seller)
    notifications = Notification.objects.all() if user.role in ["superadmin", "manager"] else Notification.objects.filter(user=user)
    data["notifications"] = notifications.order_by("-created_at")[:10]  # Show latest 10 notifications

    return data

@login_required
def superadmin_dashboard(request):
    if request.user.role != "superadmin":
        return redirect("dashboard:forbidden")  # Redirect unauthorized users

    context = get_dashboard_data(request.user)
    return render(request, "dashboard/superadmin_dashboard.html", context)


@login_required
def manager_dashboard(request):
    if request.user.role != "manager":
        return redirect("dashboard:forbidden")

    context = get_dashboard_data(request.user)
    return render(request, "dashboard/manager_dashboard.html", context)


def forbidden_view(request):
    return render(request, "base/403.html", status=403)


# 🚀✅ Removed Seller Management (Move to Sellers App)
# ✅ Seller features (Create, Edit, Delete, List) should now be handled inside the Sellers App.




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
            manager.is_staff = True  # ✅ Ensure manager is staff
            manager.set_password(form.cleaned_data["password"])  # ✅ Hash password
            manager.save()

            # ✅ Ensure user is in the "Manager" group
            manager_group, _ = Group.objects.get_or_create(name="Manager")
            manager.groups.add(manager_group)

            messages.success(request, "✅ Manager created successfully!")
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
    return render(request, "sales/sales.html")
