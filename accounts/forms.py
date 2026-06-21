from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import check_password

from .models import User

INPUT_CLASSES = (
    "w-full rounded-lg bg-[#020817] border border-cyan-900/50 px-3 py-2 text-sm "
    "text-text placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
)


def styled_text_input(**extra_attrs):
    attrs = {"class": INPUT_CLASSES}
    attrs.update(extra_attrs)
    return forms.TextInput(attrs=attrs)


def styled_password_input(**extra_attrs):
    attrs = {"class": INPUT_CLASSES}
    attrs.update(extra_attrs)
    return forms.PasswordInput(attrs=attrs)


def styled_email_input(**extra_attrs):
    attrs = {"class": INPUT_CLASSES}
    attrs.update(extra_attrs)
    return forms.EmailInput(attrs=attrs)


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, widget=styled_text_input())
    email = forms.EmailField(widget=styled_email_input())
    password = forms.CharField(widget=styled_password_input())
    password_confirm = forms.CharField(widget=styled_password_input())

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        if password:
            password_validation.validate_password(password)
        return cleaned


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Email or Username", widget=styled_text_input())
    password = forms.CharField(widget=styled_password_input())


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=styled_email_input())


class PasswordResetConfirmForm(forms.Form):
    new_password = forms.CharField(widget=styled_password_input())
    new_password_confirm = forms.CharField(widget=styled_password_input())

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("new_password"), cleaned.get("new_password_confirm")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        if p1:
            password_validation.validate_password(p1)
        return cleaned


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=styled_password_input())
    new_password = forms.CharField(widget=styled_password_input())
    new_password_confirm = forms.CharField(widget=styled_password_input())

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        pwd = self.cleaned_data["current_password"]
        if not self.user.check_password(pwd):
            raise forms.ValidationError("Current password is incorrect.")
        return pwd

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("new_password"), cleaned.get("new_password_confirm")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        if p1:
            password_validation.validate_password(p1, user=self.user)
        return cleaned
