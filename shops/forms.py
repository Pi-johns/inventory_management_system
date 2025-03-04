from django import forms
from .models import Shop
from django import forms
from .models import BusinessPeriodConfig

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ["name", "location"]



class BusinessPeriodForm(forms.ModelForm):
    class Meta:
        model = BusinessPeriodConfig
        fields = ["period_value", "period_type"]
        widgets = {
            "period_value": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "period_type": forms.Select(attrs={"class": "form-control"}),
        }

