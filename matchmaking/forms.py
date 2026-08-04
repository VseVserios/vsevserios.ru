from django import forms

from .models import SelfSearchCriteria, UserReport


class ReportUserForm(forms.ModelForm):
    class Meta:
        model = UserReport
        fields = ("reason", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Опиши проблему (необязательно)"}),
        }


class SelfSearchCriteriaForm(forms.ModelForm):
    class Meta:
        model = SelfSearchCriteria
        fields = ("min_compatibility_percent",)
        widgets = {
            "min_compatibility_percent": forms.NumberInput(attrs={"min": 1, "max": 100}),
        }
