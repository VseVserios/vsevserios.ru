from django import forms

from .models import Profile, ProfilePhoto
from .questionnaire import SENSITIVE_SECTION_IDS, get_questionnaire_spec_for_profile


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "display_name",
            "birth_date",
            "city",
            "gender",
            "looking_for",
            "bio",
            "avatar",
        )
        labels = {
            "display_name": "Имя для отображения",
            "birth_date": "Дата рождения",
            "city": "Город",
            "gender": "Пол",
            "looking_for": "Ищу",
            "bio": "О себе",
            "avatar": "Аватар",
        }
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }


class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = ProfilePhoto
        fields = ("image",)


class _PeerRadioSelect(forms.RadioSelect):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        existing = option.get("attrs") or {}
        cls = (existing.get("class") or "").strip()
        extra = "peer sr-only"
        existing["class"] = (f"{cls} {extra}" if cls else extra).strip()
        option["attrs"] = existing
        return option


class _PeerCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        existing = option.get("attrs") or {}
        cls = (existing.get("class") or "").strip()
        extra = "peer sr-only"
        existing["class"] = (f"{cls} {extra}" if cls else extra).strip()
        option["attrs"] = existing
        return option


class QuestionnaireForm(forms.Form):
    def __init__(self, *args, profile: Profile, kind: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.kind = kind

        if kind == "me":
            initial_answers = profile.questionnaire_me or {}
        elif kind == "ideal":
            initial_answers = profile.questionnaire_ideal or {}
        else:
            raise ValueError("Invalid questionnaire kind")

        spec = get_questionnaire_spec_for_profile(profile, kind)

        self._question_ids = []
        self._sensitive_question_ids = set()
        for section in spec:
            is_sensitive_section = section["id"] in SENSITIVE_SECTION_IDS
            for q in section["questions"]:
                qid = q["id"]
                self._question_ids.append(qid)
                if is_sensitive_section:
                    self._sensitive_question_ids.add(qid)
                input_type = (q.get("input_type") or "choice").strip().lower()
                is_multiple = (kind == "ideal") and bool(q.get("is_multiple"))
                choices = q.get("choices") or []

                if input_type == "text" or not choices:
                    self.fields[qid] = forms.CharField(
                        required=False,
                        widget=forms.Textarea(attrs={"rows": 4}),
                        initial=initial_answers.get(qid, ""),
                    )
                elif is_multiple:
                    initial = initial_answers.get(qid) or []
                    if not isinstance(initial, (list, tuple, set)):
                        initial = [initial]
                    self.fields[qid] = forms.MultipleChoiceField(
                        choices=choices,
                        required=False,
                        widget=_PeerCheckboxSelectMultiple(),
                        initial=list(initial),
                    )
                else:
                    self.fields[qid] = forms.ChoiceField(
                        choices=choices,
                        required=False,
                        widget=_PeerRadioSelect(),
                        initial=initial_answers.get(qid, ""),
                    )

        self.has_sensitive_section = kind == "me" and bool(
            self._sensitive_question_ids)
        if self.has_sensitive_section:
            self.fields["special_category_consent"] = forms.BooleanField(
                required=False,
                initial=profile.user.special_category_consent,
            )

    def cleaned_answers(self) -> dict:
        consent_given = bool(self.cleaned_data.get(
            "special_category_consent")) if self.has_sensitive_section else True
        answers = {}
        for qid in self._question_ids:
            if qid in self._sensitive_question_ids and not consent_given:
                continue
            v = self.cleaned_data.get(qid)
            if v is None:
                continue
            if isinstance(v, (list, tuple, set)):
                items = [str(x).strip()
                         for x in v if x is not None and str(x).strip() != ""]
                if items:
                    answers[qid] = items
                continue
            if str(v).strip() != "":
                answers[qid] = v
        return answers

    def save(self):
        answers = self.cleaned_answers()
        if self.kind == "me":
            self.profile.questionnaire_me = answers
        elif self.kind == "ideal":
            self.profile.questionnaire_ideal = answers
        else:
            raise ValueError("Invalid questionnaire kind")
        self.profile.save(
            update_fields=[f"questionnaire_{self.kind}", "updated_at"])

        if self.has_sensitive_section:
            from django.utils import timezone

            from accounts.models import ConsentEvent

            user = self.profile.user
            consent_given = bool(self.cleaned_data.get(
                "special_category_consent"))
            if consent_given and not user.special_category_consent:
                user.special_category_consent = True
                user.special_category_consent_at = timezone.now()
                user.special_category_consent_revoked_at = None
                user.save(update_fields=[
                    "special_category_consent",
                    "special_category_consent_at",
                    "special_category_consent_revoked_at",
                ])
                ConsentEvent.objects.create(
                    user=user, kind=ConsentEvent.Kind.SPECIAL_CATEGORY_GIVEN)

        return self.profile
