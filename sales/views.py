import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Sale, SaleItem
from .serializers import SaleSerializer
from notifications.views import send_notification
from reportlab.pdfgen import canvas
from io import BytesIO
from .forms import SaleForm
from sellers.models import Seller
from shops.models import Shop
from django.db.models import Q


# 🔹 List all sales with filtering (Superadmin & Manager)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@login_required
def sales_list(request):
    # Restrict access to only Superadmins and Managers
    if request.user.role not in ['superadmin', 'manager']:
        return Response({"error": "Unauthorized"}, status=403)

    sales = Sale.objects.all()

    # Get filter values from request
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    seller_filter = request.GET.get('seller', '')
    shop_id = request.GET.get('shop')


    # Apply filters based on provided values
    if status_filter:
        if status_filter == "paid":
            sales = sales.filter(balance=0)
        elif status_filter == "credit":
            sales = sales.filter(amount_paid=0)
        elif status_filter == "partial":
            sales = sales.exclude(balance=0).exclude(amount_paid=0)

    if date_filter:
        sales = sales.filter(date__date=date_filter)

    if shop_id:
        sales = sales.filter(shop_id=shop_id)

    if seller_filter:
        sales = sales.filter(seller_id=seller_filter)

    # Fetch all sellers for dropdown filter
    sellers = Seller.objects.all()
    shops = Shop.objects.all()


    return render(request, "sales/sales.html", {
        "sales": sales,
        "sellers": sellers,
    })
# 🔹 View, Edit, Delete a sale
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    if request.user.role == 'seller' and sale.seller != request.user:
        return Response({"error": "Unauthorized"}, status=403)
    
    if request.method == 'GET':
        serializer = SaleSerializer(sale)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SaleSerializer(sale, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            send_notification(None, f"Sale updated by {request.user.username} (Sale ID: {sale.id}).")
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        sale.delete()
        send_notification(None, f"Sale deleted by {request.user.username} (Sale ID: {sale_id}).")
        return Response({"message": "Sale deleted"}, status=204)

# 🔹 Record a Sale (Cash or Credit in one form)
@login_required

def record_sale(request):
    """ Allows sellers to record a sale (cash, partial, or credit) """
    if request.user.role != "seller":
        messages.error(request, "Unauthorized access!")
        return redirect("seller_dashboard")

    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.seller = request.user  # Assign the seller to the logged-in user

            # Fetch Product
            product = sale.product
            quantity = sale.quantity
            price_per_piece = sale.price_per_piece
            amount_paid = sale.amount_paid

            # Calculate Total Amount
            total_amount = quantity * price_per_piece
            balance = total_amount - amount_paid

            # Determine Payment Status
            if amount_paid == 0:
                sale.payment_status = "credit"  # Full credit sale
            elif amount_paid < total_amount:
                sale.payment_status = "partial"  # Partial payment
            else:
                sale.payment_status = "paid"  # Fully paid

            # Check Stock Availability
            if product.stock < quantity:
                messages.error(request, f"Not enough stock for {product.name}!")
                return redirect("record_sale")

            # Reduce Stock
            product.stock -= quantity
            product.save()

            # Save Sale
            sale.total_amount = total_amount
            sale.balance = balance
            sale.save()

            # Save Sale Item
            SaleItem.objects.create(sale=sale, product=product, quantity=quantity, price=price_per_piece)

            # Send Notification to Manager & Superadmin (Optional)
            # send_notification(None, f"New sale recorded by {request.user.username} (Sale ID: {sale.id}).")

            messages.success(request, "Sale recorded successfully!")
            return redirect("sales_list")  # Redirect to Sales List after success
    else:
        form = SaleForm()

    return render(request, "sales/record_sale.html", {"form": form})

# 🔹 Sales Dashboard View
def sales_dashboard(request):
    return render(request, 'sales/sales.html')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_csv(request, sale_id):
    """Exports a specific sale as a CSV file."""
    sale = get_object_or_404(Sale, id=sale_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sale_{sale_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Seller', 'Total Amount', 'Amount Paid', 'Balance', 'Date'])
    writer.writerow([sale.id, sale.seller.username, sale.total_amount, sale.amount_paid, sale.balance, sale.date])

    writer.writerow([])
    writer.writerow(['Product Name', 'Quantity', 'Price Per Unit', 'Total Price'])

    for item in sale.saleitem_set.all():
        writer.writerow([item.product.name, item.quantity, item.price, item.total_price])

    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_pdf(request, sale_id):
    """Generates a PDF report of a sale."""
    sale = get_object_or_404(Sale, id=sale_id)

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    # Sale Details
    p.drawString(100, 800, f"Sale Report - Sale ID: {sale.id}")
    p.drawString(100, 780, f"Seller: {sale.seller.username}")
    p.drawString(100, 760, f"Total Amount: ${sale.total_amount}")
    p.drawString(100, 740, f"Amount Paid: ${sale.amount_paid}")
    p.drawString(100, 720, f"Balance: ${sale.balance}")
    p.drawString(100, 700, f"Date: {sale.date.strftime('%Y-%m-%d %H:%M:%S')}")

    p.drawString(100, 660, "Products Sold:")
    
    y = 640
    for item in sale.saleitem_set.all():
        p.drawString(100, y, f"{item.product.name} - {item.quantity} x ${item.price} = ${item.total_price}")
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sale_{sale_id}.pdf"'
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_print(request, sale_id):
    """Returns sale details as JSON for printing."""
    sale = get_object_or_404(Sale, id=sale_id)

    sale_data = {
        "id": sale.id,
        "seller": sale.seller.username,
        "total_amount": float(sale.total_amount),
        "amount_paid": float(sale.amount_paid),
        "balance": float(sale.balance),
        "date": sale.date.strftime('%Y-%m-%d %H:%M:%S'),
        "items": [
            {
                "product": item.product.name,
                "quantity": item.quantity,
                "price": float(item.price),
                "total_price": float(item.total_price)
            }
            for item in sale.saleitem_set.all()
        ]
    }

    return JsonResponse(sale_data)
