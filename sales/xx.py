
@login_required
def record_sale(request):
    user = request.user
    print(f"🔍 DEBUG - User: {user}")

    # Check if user is a seller
    try:
        seller = Seller.objects.get(user=user)
        print(f"✅ DEBUG - Seller Found: {seller}")
    except Seller.DoesNotExist:
        messages.error(request, "You do not have permission to record sales.")
        logger.warning("❌ DEBUG - User %s is not a seller.", user)
        print(f"❌ DEBUG - User {user} is not a seller.")
        return redirect('sales:sales_list')

    # Get assigned shop
    shop = seller.shop
    if not shop:
        messages.error(request, "You must be assigned to a shop before making a sale.")
        logger.warning("❌ DEBUG - Seller %s has no assigned shop.", seller)
        print(f"❌ DEBUG - Seller {seller} has no assigned shop.")
        return redirect('sales:sales_list')

    print(f"✅ DEBUG - Seller's Assigned Shop: {shop.name}")

    # Get products available in the assigned shop
    products = Product.objects.all()

    if request.method == 'POST':
        print(f"🔹 DEBUG - Processing Sale Submission...")
        print(f"🔍 DEBUG - Full POST Data: {request.POST}")

        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        product_ids = request.POST.getlist('product[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price_per_piece[]')
        amount_paid = request.POST.get('amount_paid', '0').strip()

        try:
            amount_paid = Decimal(amount_paid) if amount_paid else Decimal("0.00")
        except ValueError:
            messages.error(request, "Invalid amount paid. Please enter a valid number.")
            print(f"❌ DEBUG - Invalid amount_paid value: {request.POST.get('amount_paid')}")
            return redirect('sales:record_sale')

        if not product_ids or not quantities:
            messages.error(request, "Please select at least one product.")
            print("❌ DEBUG - No products selected.")
            return redirect('sales:record_sale')

        print(f"✅ DEBUG - Selected Products: {product_ids}")

        # Stock validation
        for product_id, quantity in zip(product_ids, quantities):
            try:
                product = Product.objects.get(id=product_id)
                if product.stock_quantity < int(quantity):
                    messages.error(request, f"Not enough stock for {product.name}. Available: {product.stock_quantity}")
                    print(f"❌ DEBUG - Not enough stock for {product.name}. Available: {product.stock_quantity}")
                    return redirect('sales:record_sale')
            except Product.DoesNotExist:
                messages.error(request, "One or more selected products do not exist.")
                print(f"❌ DEBUG - Product with ID {product_id} does not exist in shop {shop.name}.")
                return redirect('sales:record_sale')

        try:
            with transaction.atomic():
                print("✅ DEBUG - Creating Sale Entry...")

                sale = Sale.objects.create(
                    seller=user,  
                    shop=shop,  
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    amount_paid=amount_paid,
                    grand_total=Decimal(0),
                    balance=Decimal(0),
                    payment_status="pending"
                )
                sale.save()  # ✅ Save first to get a primary key
                sale.update_totals()  # ✅ Now call update_totals()
                sale.save() 

                print(f"✅ DEBUG - Sale Created: ID {sale.id}")

                grand_total = Decimal("0.00")

                print("✅ DEBUG - Processing Sale Items...")

                for product_id, quantity, price in zip(product_ids, quantities, prices):
                    product = Product.objects.get(id=product_id)
                    quantity = int(quantity)
                    price = Decimal(price)
                    total_price = Decimal(quantity) * price

                    print(f"✅ DEBUG - Adding SaleItem: Product {product.name} | Quantity {quantity} | Price {price}")

                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        price=price
                    )

                    product.stock_quantity -= quantity
                    product.save()

                    print(f"✅ DEBUG - Product Sold: {product.name} | Quantity: {quantity} | Stock Left: {product.stock_quantity}")

                    grand_total += total_price

                sale.grand_total = grand_total
                sale.balance = sale.grand_total - amount_paid

                if sale.balance == Decimal(0):
                    sale.payment_status = "paid"
                elif amount_paid > Decimal(0):
                    sale.payment_status = "partial"
                else:
                    sale.payment_status = "credit"

                sale.save()

                print(f"✅ DEBUG - Final Sale Data: Grand Total: {sale.grand_total} | Balance: {sale.balance} | Payment Status: {sale.payment_status}")

                messages.success(request, "Sale recorded successfully!")
                print("✅ DEBUG - Sale Completed Successfully!")
                return redirect('sales:sales_list')

        except Exception as e:
            messages.error(request, f"Error: {e}")
            print(f"❌ DEBUG - Exception occurred: {str(e)}")
            return redirect('sales:record_sale')

    return render(request, 'sales/record_sale.html', {'products': products, 'shop': shop})
