from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Profile, WithdrawalRequest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.forms import PasswordChangeForm
from .models import IdentityVerification
from django.forms import TextInput, EmailInput, DateTimeInput


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'referral_code',)
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'referral_code': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


class CustomAuthenticationForm(AuthenticationForm):

    class Meta:
        model = CustomUser


class ProfileForm(forms.ModelForm):
    username = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    registration_date = forms.DateTimeField(required=False)

    class Meta:
        model = Profile
        fields = ['usdt_erc20_wallet_address']
        widgets = {
            'usdt_erc20_wallet_address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.user:
            user = instance.user
            self.fields['username'].initial = user.username
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['registration_date'].initial = user.date_joined

            # Set fields as read-only
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['first_name'].widget.attrs['readonly'] = True
            self.fields['last_name'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['registration_date'].widget.attrs['readonly'] = True

    def clean_usdt_erc20_wallet_address(self):
        usdt_address = self.cleaned_data['usdt_erc20_wallet_address']
        if usdt_address and not re.match(r'^0x[a-fA-F0-9]{40}$', usdt_address):
            raise forms.ValidationError("Invalid USDT ERC20 address.")
        return usdt_address


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Old Password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))


class WithdrawalRequestForm(forms.ModelForm):
    class Meta:
        model = WithdrawalRequest
        fields = ['amount', 'currency', 'to_address']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(choices=[('USDT', 'USDT')], attrs={'class': 'form-select'}),
            'to_address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class IdentityVerificationForm(forms.ModelForm):
    class Meta:
        model = IdentityVerification
        fields = ['ssn', 'zip_code', 'full_name', 'address', 'state', 'document_type', 'document_front', 'document_back']
        widgets = {
            'ssn': forms.TextInput(attrs={'placeholder': 'Social Security Number', 'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'Zip Code', 'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'placeholder': 'Address', 'class': 'form-control'}),
            'state': forms.TextInput(attrs={'placeholder': 'State', 'class': 'form-control'}),
            'document_type': forms.Select(choices=[
                ('driver_license', 'Driver\'s License'),
                ('passport', 'Passport'),
                ('id_card', 'ID Card')
            ], attrs={'class': 'form-select'}),
            'document_front': forms.FileInput(attrs={'class': 'forms'}),
            'document_back': forms.FileInput(attrs={'class': 'forms'}),
        }

    def __init__(self, *args, **kwargs):
        super(IdentityVerificationForm, self).__init__(*args, **kwargs)
