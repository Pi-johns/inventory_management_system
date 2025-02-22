from django import forms
from django.contrib.auth import get_user_model
from .models import Seller
from shops.models import Shop

User = get_user_model()

class SellerForm(forms.ModelForm):
    """ Form for creating a new seller. """
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={"class": "w-full px-3 py-2 border rounded"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "w-full px-3 py-2 border rounded"}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={"class": "w-full px-3 py-2 border rounded"}))
    shop = forms.ModelChoiceField(queryset=Shop.objects.all(), required=True, widget=forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "w-full px-3 py-2 border rounded"}), required=True)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={"class": "w-full px-3 py-2 border rounded"}), required=True)

    class Meta:
        model = Seller
        fields = ["username", "email", "phone", "shop", "password", "password2"]

    def clean(self):
        """ Validate password confirmation """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            self.add_error("password2", "Passwords do not match!")

        return cleaned_data
