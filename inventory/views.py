from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Product, StockLog
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
            messages.success(request, "Product added successfully!")

            # 🔹 Notify Superadmins & Managers about the new product
            send_notification(None, f"New product added: {product.name}.")

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
def product_list(request):
    """Managers see full stock details, sellers see only stock levels."""
    products = Product.objects.all()

    # 🔹 Check for low-stock alerts and notify managers
    for product in products:
        if product.stock < product.low_stock_threshold:
            send_notification(None, f"Low stock alert: {product.name} (Remaining: {product.stock}).")

    return render(request, "inventory/inventory.html", {"products": products})
