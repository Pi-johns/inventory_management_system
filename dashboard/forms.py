from django import forms
from shops.models import Shop
from accounts.models import CustomUser
from sellers.models import Seller


class SellerForm(forms.ModelForm):
    phone = forms.CharField(max_length=15, required=True)
    shop = forms.ModelChoiceField(queryset=Shop.objects.all(), required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "phone", "password",]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "seller"  # Ensure the role is seller
        if commit:
            user.save()
            # Create SellerProfile with selected shop
            Seller.objects.create(user=user, shop=self.cleaned_data["shop"], phone=self.cleaned_data["phone"])
        return user
    

class ManagerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.set_password(self.cleaned_data["password"])
            user.save()
        return user