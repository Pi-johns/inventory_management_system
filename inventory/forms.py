from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "entry_price", "stock_quantity", "low_stock_threshold"]
