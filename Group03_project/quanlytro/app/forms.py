from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import *

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        exclude = ['created_at', 'updated_at']

class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        exclude = ['created_at', 'updated_at']