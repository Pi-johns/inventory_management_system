from django.urls import path
from .views import (
    superadmin_dashboard, manager_dashboard,  
    forbidden_view,  manager_list,
        create_manager, edit_manager, delete_manager, sales_dashboard)

app_name = "dashboard"

urlpatterns = [
    path("sales/", sales_dashboard, name="sales_dashboard"),
    path("superadmin/", superadmin_dashboard, name="superadmin_dashboard"),
    path("manager/", manager_dashboard, name="manager_dashboard"),
    path("forbidden/", forbidden_view, name="forbidden"),
    path("superadmin/dashboard/", superadmin_dashboard, name="superadmin_dashboard"),
    path("manager/dashboard/", manager_dashboard, name="manager_dashboard"),
    path("managers/", manager_list, name="manager_list"),
    path("managers/create/", create_manager, name="create_manager"),
    path("managers/edit/<int:manager_id>/", edit_manager, name="edit_manager"),
    path("managers/delete/<int:manager_id>/", delete_manager, name="delete_manager"),
]

