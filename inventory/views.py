from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Product
from django.db import models
from .forms import ProductForm



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

    return redirect("inventory:product_list")

@login_required
def product_list(request):
    """Managers see full stock details, sellers see only stock levels with search functionality."""
    
    # Get search query
    query = request.GET.get("q")

    # 🔍 Filter products by search query if provided
    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()

    # 🔹 Categorize stock levels
    low_stock_products = products.filter(stock_quantity__lt=5)  # Adjust threshold as needed
    out_of_stock_products = products.filter(stock_quantity=0)

    # Store notified products in session to prevent repeated alerts
    if "notified_products" not in request.session:
        request.session["notified_products"] = []

    for product in low_stock_products:
        if product.id not in request.session["notified_products"]:
            request.session["notified_products"].append(product.id)  # Mark as notified
    
    # 🛒 Calculate current stock value for each product and total stock value
    for product in products:
        product.current_stock_value = product.stock_quantity * product.entry_price
    
    total_stock_value = sum(product.current_stock_value for product in products)

    context = {
        "products": products,
        "query": query,
        "total_stock_value": total_stock_value,  # Pass to template
        "low_stock_products": low_stock_products,
        "total_low_stock": low_stock_products.count(),
        "critical_stock": low_stock_products.filter(stock_quantity__lte=2).count(),
        "out_of_stock_products": out_of_stock_products,
        "total_out_of_stock": out_of_stock_products.count(),
    }
    return render(request, "inventory/inventory.html", context)

@login_required
def low_stock_products_list(request):
    """List all products below the stock threshold"""
    threshold = 5  # Adjust threshold as needed
    low_stock_products = Product.objects.filter(stock_quantity__lt=threshold)

    context = {
        "low_stock_products": low_stock_products,
        "total_low_stock": low_stock_products.count(),
        "critical_stock": low_stock_products.filter(stock_quantity__lte=2).count(),
    }
    return render(request, "inventory/low_products_list.html", context)



@login_required
def out_of_stock_products(request):
    """Fetch all products that are completely out of stock"""
    out_of_stock_products = Product.objects.filter(stock_quantity=0)

    context = {
        "out_of_stock_products": out_of_stock_products,
        "total_out_of_stock": out_of_stock_products.count(),
    }
    return render(request, "inventory/outstock.html", context)


