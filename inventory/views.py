from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Product
from django.db import models
from .forms import ProductForm
from notifications.views import send_notification


def is_manager(user):
    return user.is_authenticated and user.role == "manager"

def is_seller(user):
    return user.is_authenticated and user.role == "seller"


@login_required
@user_passes_test(is_manager)
def add_product(request):
    """Allows managers to add products and sends a notification."""
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, "✅ Product added successfully!")

            # 🔹 Notify Superadmins & Managers about the new product
            send_notification(None, f"🆕 New product added: {product.name}.")
            print("DEBUG: Redirecting to product list")

            return redirect("inventory:product_list")
    else:
        form = ProductForm()
    
    return render(request, "inventory/add_product.html", {"form": form})
@login_required
@user_passes_test(is_manager)

def update_product(request, product_id):
    """Allows managers to update products and sends a notification."""
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Product '{product.name}' updated successfully!")

            # 🔹 Notify Superadmins & Managers about the product update
            send_notification(None, f"🔄 Product updated: {product.name}.")

            return redirect("inventory:product_list")  # Ensure this matches your `urls.py`
    else:
        form = ProductForm(instance=product)

    return render(request, "inventory/update_product.html", {"form": form, "product": product})
@login_required
@user_passes_test(is_manager)
def delete_product(request, product_id):
    """Allows managers to delete products and sends a notification."""
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name  # Store name before deletion
    product.delete()
    messages.success(request, "Product deleted successfully!")

    # 🔹 Notify Superadmins & Managers about the product deletion
    send_notification(None, f"Product deleted: {product_name}.")

    return redirect("inventory:product_list")

@login_required
@user_passes_test(is_manager)
def product_list(request):
    """Managers see full stock details, sellers see only stock levels with search functionality."""
    
    # Get search query
    query = request.GET.get("q")

    # 🔍 Filter products by search query if provided
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()

    # 🔹 Low Stock Alerts - Avoid Duplicate Notifications
    low_stock_products = products.filter(stock_quantity__lt=models.F("low_stock_threshold"))
    
    # Store notified products in session to prevent repeated alerts
    if "notified_products" not in request.session:
        request.session["notified_products"] = []

    for product in low_stock_products:
        if product.id not in request.session["notified_products"]:
            send_notification(None, f"⚠️ Low stock alert: {product.name} (Remaining: {product.stock_quantity}).")
            request.session["notified_products"].append(product.id)  # Mark as notified

    context = {
        "products": products,
        "query": query,
    }
    return render(request, "inventory/inventory.html", context)