from django import forms
from .models import Sale

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "shop", "customer_name", "customer_phone", "quantity", "price_per_piece", "amount_paid", "payment_status"]
        widgets = {
            "payment_status": forms.HiddenInput()  # Hide field since it's auto-calculated
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get("quantity")
        price_per_piece = cleaned_data.get("price_per_piece")
        amount_paid = cleaned_data.get("amount_paid", 0)  # Default to 0 if empty

        if quantity and price_per_piece:
            total_amount = quantity * price_per_piece
            balance = total_amount - amount_paid

            if amount_paid > total_amount:
                raise forms.ValidationError("Amount paid cannot be more than the total amount.")

            # Automatically determine payment status
            if amount_paid == 0:
                cleaned_data["payment_status"] = "Credit"
            elif balance == 0:
                cleaned_data["payment_status"] = "Paid"
            else:
                cleaned_data["payment_status"] = "Partial"

        return cleaned_data
