from django import forms
from .models import Sale, SaleItem
from inventory.models import Product  # To check stock
from shops.models import Shop  # ✅ Import Shop model

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'price_per_piece']

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        product = self.cleaned_data.get('product')

        if quantity <= 0:
            raise forms.ValidationError("Quantity must be at least 1.")

        if product and quantity > product.stock:
            raise forms.ValidationError(f"Only {product.stock} left in stock.")

        return quantity

    def clean_price_per_piece(self):
        price_per_piece = self.cleaned_data.get('price_per_piece')
        if price_per_piece <= 0:
            raise forms.ValidationError("Price per piece must be positive.")
        return price_per_piece


class SaleForm(forms.ModelForm):
    shop = forms.ModelChoiceField(
        queryset=Shop.objects.all(),
        required=False,  # ✅ Required only for Managers & Superadmins
        empty_label="Select a Shop",
        label="Shop"
    )

    class Meta:
        model = Sale
        fields = ['customer_name', 'customer_phone', 'amount_paid', 'shop']  # ✅ Shop included

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # ✅ Get user from view
        super().__init__(*args, **kwargs)

        if self.user and self.user.role == "Seller":
            # ✅ Sellers CANNOT select a shop (auto-assigned)
            self.fields.pop('shop')

    def clean_customer_name(self):
        name = self.cleaned_data.get('customer_name', '').strip()
        if not name:
            raise forms.ValidationError("Customer name is required.")
        return name

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '').strip()
        if not phone.isdigit():
            raise forms.ValidationError("Customer phone must be numeric.")
        if len(phone) < 7 or len(phone) > 15:
            raise forms.ValidationError("Enter a valid phone number (7-15 digits).")
        return phone

    def clean_amount_paid(self):
        amount_paid = self.cleaned_data.get('amount_paid')
        if amount_paid is None:
            raise forms.ValidationError("Amount paid cannot be empty.")
        if amount_paid < 0:
            raise forms.ValidationError("Amount paid cannot be negative.")
        return amount_paid

    def clean(self):
        cleaned_data = super().clean()

        if self.user:
            if self.user.role == "Seller":
                # ✅ Ensure seller has an assigned shop
                if not self.user.shop:
                    raise forms.ValidationError("Sellers must be assigned to a shop before recording sales.")
                # ✅ Set shop automatically for sellers
                cleaned_data['shop'] = self.user.shop

            elif self.user.role in ["Manager", "Superadmin"]:
                # ✅ Managers & Superadmins MUST select a shop
                if not cleaned_data.get('shop'):
                    raise forms.ValidationError("Managers and Superadmins must select a shop.")

        return cleaned_data
