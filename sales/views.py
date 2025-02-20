import csv
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Sale, SaleItem, CreditSale
from .serializers import SaleSerializer
from notifications.views import send_notification
from reportlab.pdfgen import canvas
from io import BytesIO



# 🔹 List all sales (Superadmin)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sales_list(request):
    if request.user.role != 'superadmin':
        return Response({"error": "Unauthorized"}, status=403)

    sales = Sale.objects.all()
    serializer = SaleSerializer(sales, many=True)
    return Response(serializer.data)

# 🔹 View, Edit, Delete a specific sale
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # 🔹 Allow only sellers to edit/delete their own sales
    if request.user.role == 'seller' and sale.seller != request.user:
        return Response({"error": "Unauthorized"}, status=403)

    if request.method == 'GET':
        serializer = SaleSerializer(sale)
        return Response(serializer.data)

    elif request.method == 'PUT':  # 🔹 Edit Sale
        serializer = SaleSerializer(sale, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Notify Admins about sale update
            send_notification(None, f"Sale updated by {request.user.username} (Sale ID: {sale.id}).")

            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':  # 🔹 Delete Sale
        sale.delete()

        # Notify Admins about sale deletion
        send_notification(None, f"Sale deleted by {request.user.username} (Sale ID: {sale_id}).")

        return Response({"message": "Sale deleted"}, status=204)

# 🔹 Print Sale Receipt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_print(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    sale_data = {
        "id": sale.id,
        "seller": sale.seller.username,
        "total_amount": float(sale.total_amount),
        "date": sale.date.strftime('%Y-%m-%d %H:%M:%S'),
        "items": [
            {"product": item.product.name, "quantity": item.quantity, "price": float(item.price)}
            for item in sale.saleitem_set.all()
        ]
    }

    return JsonResponse(sale_data)

# 🔹 Export Sale as PDF
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_pdf(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Create a PDF buffer
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    # Write sale details into the PDF
    p.drawString(100, 800, f"Sale Report - Sale ID: {sale.id}")
    p.drawString(100, 780, f"Seller: {sale.seller.username}")
    p.drawString(100, 760, f"Total Amount: ${sale.total_amount}")
    p.drawString(100, 740, f"Date: {sale.date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    p.drawString(100, 700, "Products Sold:")
    
    y = 680
    for item in sale.saleitem_set.all():
        p.drawString(100, y, f"{item.product.name} - {item.quantity} x ${item.price}")
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)

    # Send the PDF as response
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sale_{sale_id}.pdf"'
    return response

# 🔹 Export Sale as CSV
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sale_csv(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Create a CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sale_{sale_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Seller', 'Total Amount', 'Date'])
    writer.writerow([sale.id, sale.seller.username, sale.total_amount, sale.date])

    writer.writerow([])
    writer.writerow(['Product Name', 'Quantity', 'Price'])

    for item in sale.saleitem_set.all():
        writer.writerow([item.product.name, item.quantity, item.price])

    return response
# 🔹 Record a New Sale (Seller)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_sale(request):
    if request.user.role != 'seller':
        return Response({"error": "Unauthorized"}, status=403)

    serializer = SaleSerializer(data=request.data)
    if serializer.is_valid():
        sale = serializer.save(seller=request.user)

        # Notify Admins about the new sale
        send_notification(None, f"New sale recorded by {request.user.username} (Sale ID: {sale.id}).")

        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

# 🔹 Record a Credit Sale (Seller)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recordcredit_sale(request):
    if request.user.role != 'seller':
        return Response({"error": "Unauthorized"}, status=403)

    serializer = SaleSerializer(data=request.data)
    if serializer.is_valid():
        sale = serializer.save(seller=request.user)

        # Notify Admins about the new credit sale
        send_notification(None, f"New credit sale recorded by {request.user.username} (Sale ID: {sale.id}).")

        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

def sales_dashboard(request):
    """Directs user to Sales Management Dashboard."""
    return render(request, 'sales/sales.html')