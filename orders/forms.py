import re

from django import forms

from accounts.forms import style_fields
from .models import Order


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=120, label="Full name")
    phone = forms.CharField(max_length=15, label="Contact number")
    address = forms.CharField(
        label="Delivery address", min_length=10, max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    payment_method = forms.ChoiceField(
        label="Payment method", choices=Order.PaymentMethod.choices,
        initial=Order.PaymentMethod.COD, widget=forms.RadioSelect,
    )
    note = forms.CharField(required=False, max_length=200, label="Note for the restaurant (optional)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_phone(self):
        phone = re.sub(r"[\s-]", "", self.cleaned_data["phone"])
        if not re.fullmatch(r"\+?\d{10,13}", phone):
            raise forms.ValidationError("Enter a valid phone number (10-13 digits).")
        return phone
