
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Expense
from .forms import ExpenseForm  # Create this form
from django.utils.timezone import now
from django.db.models import Sum, Count

@login_required
def enter_expense(request):
    """View for managers to manually enter business expenses."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to add expenses.")
        return redirect("inventory:product_list")

    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.recorded_by = request.user  # Store who recorded it
            expense.date_recorded = now()
            expense.save()
            messages.success(request, "Expense recorded successfully!")
            return redirect("expenses:expense_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExpenseForm()

    return render(request, "expenses/enter_expense.html", {"form": form})




@login_required
def expense_list(request):
    """View to display all recorded expenses with a summary."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to view expenses.")
        return redirect("inventory:product_list")

    # Get current business period start (adjust based on your period logic)
    current_period_start = now().replace(day=1)  # Example: Start of the month

    # Filter expenses within the current period
    expenses = Expense.objects.filter(date_recorded__gte=current_period_start).order_by("-date_recorded")

    # Summary calculations
    total_expenses = expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    num_expenses = expenses.count()
    last_expense_date = expenses.first().date_recorded if expenses.exists() else None

    context = {
        "expenses": expenses,
        "total_expenses": total_expenses,
        "num_expenses": num_expenses,
        "last_expense_date": last_expense_date,
    }

    return render(request, "expenses/expense_list.html", context)
