from django import forms

from .models import UserReport


class ReportUserForm(forms.ModelForm):
    class Meta:
        model = UserReport
        fields = ("reason", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Опиши проблему (необязательно)"}),
        }
