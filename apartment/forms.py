from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        # Kiểm tra email có tồn tại trong hệ thống không
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email không đúng hoặc chưa tồn tại, hãy nhập lại.")
        return email