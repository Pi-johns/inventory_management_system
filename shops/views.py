from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Shop
from .forms import ShopForm
from django.http import JsonResponse
from .models import BusinessPeriodConfig
from .forms import BusinessPeriodForm
from datetime import date

def is_manager_or_superadmin(user):
    return user.is_authenticated and user.role in ["manager", "superadmin"]

@login_required
@user_passes_test(is_manager_or_superadmin)
def add_shop(request):
    if request.method == "POST":
        form = ShopForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Shop added successfully!")
            return redirect("shops:shop_list")
    else:
        form = ShopForm()
    return render(request, "shops/add_shop.html", {"form": form})

@login_required
def shop_list(request):
    shops = Shop.objects.all()
    return render(request, "shops/shop_list.html", {"shops": shops})



@login_required
def create_shop(request):
    if request.user.role not in ["manager", "superadmin"]:
        return redirect("shop_list")  # Restrict access

    if request.method == "POST":
        form = ShopForm(request.POST)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.created_by = request.user
            shop.save()
            return redirect("shops:shop_list")
    else:
        form = ShopForm()

    return render(request, "shops/shop_form.html", {"form": form})

@login_required
def edit_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    
    if request.user.role not in ["manager", "superadmin"]:
        return redirect("shop_list")  # Restrict access

    if request.method == "POST":
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            return redirect("shops:shop_list")
    else:
        form = ShopForm(instance=shop)

    return render(request, "shops/shop_form.html", {"form": form})

@login_required
def delete_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)

    if request.user.role not in ["manager", "superadmin"]:
        return redirect("shop_list")  # Restrict access

    if request.method == "POST":
        shop.delete()
        return redirect("shops:shop_list")

    return render(request, "shops/shop_confirm_delete.html", {"shop": shop})



@login_required
def get_shops(request):
    """Return shops for Superadmin and Managers"""
    user = request.user

    # ✅ Check authentication before printing user details
    if not user.is_authenticated:
        return JsonResponse({"error": "Unauthorized - Please login"}, status=401)

    # ✅ Improved role check for Superadmins & Managers
    is_manager = user.groups.filter(name="Manager").exists()
    is_superadmin = user.is_superuser

    print(f"✅ DEBUG - User accessing API: {user} (Superadmin: {is_superadmin}, Manager: {is_manager})")

    if is_superadmin or is_manager:
        shops = Shop.objects.values("id", "name")
        print(f"✅ DEBUG - Returning {len(shops)} shops.")
        return JsonResponse({"shops": list(shops)})
    
    print("❌ DEBUG - User does not have permission to view shops.")
    return JsonResponse({"error": "Forbidden - Access Denied"}, status=403)





@login_required
def business_period_settings(request):
    """View to allow Managers and Super Admins to configure the calculation period."""
    if not request.user.is_staff:  # Restrict Sellers
        messages.error(request, "You are not authorized to access this page.")
        return redirect("dashboard")

    period_config, created = BusinessPeriodConfig.objects.get_or_create(id=1)  # Ensure only one config exists

    if request.method == "POST":
        form = BusinessPeriodForm(request.POST, instance=period_config)
        if form.is_valid():
            period_config = form.save(commit=False)
            period_config.last_calculation_date = date.today()  # Update last calculation date
            period_config.save()
            messages.success(request, "Business calculation period updated successfully!")
            return redirect("business_period_settings")
    else:
        form = BusinessPeriodForm(instance=period_config)

    return render(request, "shops/period_setting.html", {"form": form, "period_config": period_config})


@login_required
def dashboard(request):
    """Dashboard view for Admins, Managers, and Sellers."""
    user = request.user
    period_alert = None

    # Only show alerts to Admins & Managers (not sellers)
    if user.is_staff:
        try:
            period_config = BusinessPeriodConfig.objects.get(id=1)
            remaining_days = (period_config.next_calculation_date() - date.today()).days

            # Show alert if the period is ending in 3 days or less
            if remaining_days <= 3:
                period_alert = f"⚠️ Your business performance period ends in {remaining_days} day(s)."

        except BusinessPeriodConfig.DoesNotExist:
            period_alert = None  # No settings configured yet

    return render(request, "dashboard/manager_dashboard.html", {"period_alert": period_alert})