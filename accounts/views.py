from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse



def redirect_user(user):
    """Redirect users based on their role."""
    if user.is_superuser:
        return redirect('dashboard:superadmin_dashboard')  # ✅ Redirect to Superadmin Dashboard
    elif user.is_manager:
        return redirect('dashboard:manager_dashboard')  # ✅ Redirect to Manager Dashboard
    elif user.is_seller:
        return redirect('dashboard:seller_dashboard')  # ✅ Redirect to Seller Dashboard
    return redirect('home')

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "User registered successfully!")
            return redirect("accounts:login")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect_user(request.user)  # ✅ Redirect already logged-in user

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            # 🔹 Redirect Based on Role
            if user.role == "superadmin":
                return redirect(reverse("dashboard:superadmin_dashboard"))
            elif user.role == "manager":
                return redirect(reverse("dashboard:manager_dashboard"))  # ✅ Ensure this exists
            elif user.role == "seller":
                return redirect(reverse("dashboard:seller_dashboard"))
            else:
                return redirect("home")  # Default fallback

    return render(request, "accounts/login.html")


@login_required
def user_logout(request):
    logout(request)
    return redirect('home')  # ✅ After logout, return to login page