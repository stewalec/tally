from django import forms
from .models import normalize_phone


class LoginForm(forms.Form):
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "placeholder": "(555) 555-5555",
                "autocomplete": "tel",
                "inputmode": "tel",
            }
        ),
    )

    def clean_phone_number(self):
        raw = self.cleaned_data["phone_number"]
        normalized = normalize_phone(raw)
        if not normalized:
            raise forms.ValidationError("Enter a valid US phone number.")
        return normalized


class OTPForm(forms.Form):
    code = forms.CharField(
        label="Verification Code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "placeholder": "000000",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": "[0-9]{6}",
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("Enter the 6-digit code from your SMS.")
        return code


class ProfileForm(forms.Form):
    first_name = forms.CharField(
        label="First Name",
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "First name"}),
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "Last name"}),
    )
    username = forms.SlugField(
        label="Username",
        max_length=100,
        help_text="Letters, numbers, and hyphens only. Used in your profile URL.",
        widget=forms.TextInput(attrs={"placeholder": "username"}),
    )
