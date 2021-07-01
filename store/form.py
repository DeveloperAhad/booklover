from django.forms import ModelForm, Select, TextInput, PasswordInput
from .models import Address

from django.contrib.auth import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class ShippingForm(ModelForm):
    class Meta:
        model = Address
        fields = ['full_address', 'phone', 'default']


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': TextInput(attrs={"class": "form-control input-lg mb-3", "placeholder": "Username"}),
            'email': TextInput(attrs={"class": "form-control input-lg mb-3", "placeholder": "Email"}),
        }

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = PasswordInput(attrs={'class': 'form-control input-lg mb-3', "placeholder": "Password"})
        self.fields['password2'].widget = PasswordInput(attrs={'class': 'form-control input-lg mb-4', "placeholder": "Confirm Password"})

