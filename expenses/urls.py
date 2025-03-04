from django.urls import path
from .views import enter_expense, expense_list

app_name = "expenses"

urlpatterns = [
    path("enter/expense/", enter_expense, name="enter_expense"),  # Page to enter a new expense
    path("expense/list/", expense_list, name="expense_list"),  # Page to list all expenses
]
