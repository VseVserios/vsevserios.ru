from django import forms

from .models import AdminSearchOrder, SelfSearchCriteria, UserReport


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

    def clean_min_compatibility_percent(self):
        value = self.cleaned_data["min_compatibility_percent"]
        if not 1 <= value <= 100:
            raise forms.ValidationError("Укажите процент от 1 до 100.")
        return value


def split_criteria(text: str) -> list[str]:
    parts = (text or "").replace(";", "\n").splitlines()
    return [p.strip() for p in parts if p.strip()]


class AdminSearchOrderFormMixin:
    """Проверка условий тарифов: точечный — минимум два критерия, углублённый — пожелания обязательны."""

    def clean(self):
        cleaned = super().clean()
        tier = cleaned.get("tier")
        criteria = (cleaned.get("required_criteria") or "").strip()
        cleaned["required_criteria"] = criteria

        if tier == AdminSearchOrder.Tier.TARGETED and len(split_criteria(criteria)) < 2:
            self.add_error(
                "required_criteria",
                "Для точечного подбора укажите не менее двух обязательных критериев (каждый с новой строки).",
            )
        elif tier == AdminSearchOrder.Tier.DEEP and not criteria:
            self.add_error(
                "required_criteria", "Для углублённого подбора опишите все ваши пожелания.")
        return cleaned


class ClientSearchOrderForm(AdminSearchOrderFormMixin, forms.ModelForm):
    class Meta:
        model = AdminSearchOrder
        fields = ("tier", "required_criteria")
        labels = {
            "tier": "Тариф",
            "required_criteria": "Критерии и пожелания",
        }
        widgets = {
            "required_criteria": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Точечный: не менее двух обязательных критериев, каждый с новой строки. "
                                   "Углублённый: все ваши пожелания.",
                }
            ),
        }
