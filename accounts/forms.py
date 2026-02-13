from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": "username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        from matchmaking.models import UserBan

        if UserBan.objects.active().filter(user=user).exists():
            raise forms.ValidationError(
                "Доступ ограничен: ваш аккаунт заблокирован модерацией.",
                code="banned",
            )


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class EmailVerificationForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code.isdigit():
            raise forms.ValidationError("Введите 6-значный код.")
        if len(code) != 6:
            raise forms.ValidationError("Введите 6-значный код.")
        return code


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"autocomplete": "email"}))


class PasswordResetCodeConfirmForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Введите 6-значный код.")
        return code

    def clean(self):
        cleaned = super().clean()
        p1 = (cleaned.get("new_password1") or "").strip()
        p2 = (cleaned.get("new_password2") or "").strip()

        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Пароли не совпадают.")

        if p1:
            validate_password(p1)

        return cleaned


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"autocomplete": "username"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Укажите email.")

        qs = User.objects.filter(email__iexact=email)
        if self.instance and getattr(self.instance, "pk", None):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Этот email уже занят.")
        return email


class PasswordConfirmForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data.get("password") or ""
        if not self.user or not getattr(self.user, "is_authenticated", False):
            raise forms.ValidationError("Пользователь не авторизован.")

        ok = authenticate(username=self.user.get_username(), password=password)
        if ok is None:
            raise forms.ValidationError("Неверный пароль.")
        return password
