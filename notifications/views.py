from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Notification
from shops.models import Shop  # Assuming there's a Shop model
from sellers.models import Seller  # Assuming there's a Seller model

@login_required
def all_notifications(request):
    """View to display and filter notifications based on role."""
    user = request.user
    notifications = Notification.objects.all().order_by('-created_at')

    # Get filter values from the request
    date_filter = request.GET.get('date', '').strip()
    shop_filter = request.GET.get('shop', '').strip()
    seller_filter = request.GET.get('seller', '').strip()

    # Sellers: See only their own notifications & filter by date
    if user.role == "seller":
        notifications = notifications.filter(user=user)
        if date_filter:
            notifications = notifications.filter(created_at__date=date_filter)

        # No need for shops and sellers dropdown for sellers
        shops, sellers = None, None  
        selected_shop, selected_seller = None, None

    # Managers & Superadmins: Can filter by Date, Shop, Seller (one, two, or all at once)
    else:
        if date_filter:
            notifications = notifications.filter(created_at__date=date_filter)
        if shop_filter:
            notifications = notifications.filter(shop__id=shop_filter)
        if seller_filter:
            notifications = notifications.filter(user__id=seller_filter)

        # Fetch shops and sellers for filter options
        shops = Shop.objects.all()
        sellers = Seller.objects.all()
        
        # Preserve selected values
        selected_shop = shop_filter
        selected_seller = seller_filter

    context = {
        'notifications': notifications,
        'shops': shops,
        'sellers': sellers,
        'selected_shop': selected_shop,
        'selected_seller': selected_seller,
        'selected_date': date_filter,
        'shops': shops,
        'sellers': sellers,  # Preserve selected date
    }
    return render(request, 'notifications/notifications.html', context)
