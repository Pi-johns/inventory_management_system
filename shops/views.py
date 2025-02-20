from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Shop
from accounts.models import CustomUser
from .forms import ShopForm

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