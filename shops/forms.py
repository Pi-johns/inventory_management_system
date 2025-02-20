from django import forms
from .models import Shop
from accounts.models import CustomUser

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ["name", "location"]


