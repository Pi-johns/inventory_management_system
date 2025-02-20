from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from dashboard.forms import ManagerForm

User = get_user_model()

def is_superadmin(user):
    return user.is_superadmin

@login_required
@user_passes_test(is_superadmin)
def manager_list(request):
    managers = User.objects.filter(role="manager")
    return render(request, "dashboard/manager_list.html", {"managers": managers})

@login_required
@user_passes_test(is_superadmin)
def create_manager(request):
    if request.method == "POST":
        form = ManagerForm(request.POST)
        if form.is_valid():
            manager = form.save(commit=False)
            manager.role = "manager"
            manager.set_password(form.cleaned_data["password"])
            manager.save()
            messages.success(request, "Manager created successfully!")
            return redirect("dashboard:manager_list")
    else:
        form = ManagerForm()

    return render(request, "dashboard/create_manager.html", {"form": form})

@login_required
@user_passes_test(is_superadmin)
def edit_manager(request, manager_id):
    manager = get_object_or_404(User, id=manager_id, role="manager")

    if request.method == "POST":
        form = ManagerForm(request.POST, instance=manager)
        if form.is_valid():
            form.save()
            messages.success(request, "Manager updated successfully!")
            return redirect("dashboard:manager_list")

    else:
        form = ManagerForm(instance=manager)

    return render(request, "dashboard/edit_manager.html", {"form": form, "manager": manager})

@login_required
@user_passes_test(is_superadmin)
def delete_manager(request, manager_id):
    manager = get_object_or_404(User, id=manager_id, role="manager")
    manager.delete()
    messages.success(request, "Manager deleted successfully!")
    return redirect("dashboard:manager_list")
