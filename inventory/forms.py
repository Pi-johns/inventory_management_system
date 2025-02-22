from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "entry_price", "stock_quantity", "low_stock_threshold"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full border p-2 rounded-lg"}),
            "entry_price": forms.NumberInput(attrs={"class": "w-full border p-2 rounded-lg"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "w-full border p-2 rounded-lg"}),
            "low_stock_threshold": forms.NumberInput(attrs={"class": "w-full border p-2 rounded-lg"}),
        }
