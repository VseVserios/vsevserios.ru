from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import Group

from accounts.models import User
from matchmaking.models import HomeBlock, HomePage, UserBan
from profiles.models import Profile, QuestionnaireChoice, QuestionnaireQuestion, QuestionnaireSection


class UserEditForm(forms.ModelForm):
    is_matchmaker = forms.BooleanField(required=False)

    def __init__(self, *args, actor: User | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        if actor and not actor.is_superuser:
            self.fields["is_staff"].disabled = True

        try:
            self.fields["is_matchmaker"].initial = bool(
                self.instance
                and self.instance.pk
                and self.instance.groups.filter(name="matchmaker").exists()
            )
        except Exception:
            self.fields["is_matchmaker"].initial = False

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Ensure group membership is updated even when commit=False.
        # The caller is expected to save the user instance if needed.
        is_matchmaker = bool(self.cleaned_data.get("is_matchmaker"))
        group, _ = Group.objects.get_or_create(name="matchmaker")
        if is_matchmaker:
            user.groups.add(group)
        else:
            user.groups.remove(group)

        return user

    class Meta:
        model = User
        fields = ("username", "email", "is_active", "is_staff")


class UserSetPasswordForm(SetPasswordForm):
    pass


class ProfileEditForm(forms.ModelForm):
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
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }


class UserBanForm(forms.ModelForm):
    class Meta:
        model = UserBan
        fields = (
            "user",
            "reason",
            "expires_at",
            "note",
        )
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }


class QuestionnaireSectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["code"].disabled = True

    class Meta:
        model = QuestionnaireSection
        fields = ("code", "gender", "title", "show_in_me", "show_in_ideal", "order")


class QuestionnaireQuestionForm(forms.ModelForm):
    input_type = forms.ChoiceField(
        choices=(
            ("choice", "С вариантами"),
            ("text", "Свободный ввод"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["code"].disabled = True

        self.fields["input_type"].initial = (getattr(self.instance, "input_type", "") or "choice")

    class Meta:
        model = QuestionnaireQuestion
        fields = (
            "code",
            "gender",
            "text",
            "input_type",
            "is_multiple",
            "show_in_me",
            "show_in_ideal",
            "order",
        )


class QuestionnaireChoiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["value"].disabled = True

    class Meta:
        model = QuestionnaireChoice
        fields = ("value", "label", "order")


class UserBanForUserForm(forms.ModelForm):
    class Meta:
        model = UserBan
        fields = (
            "reason",
            "expires_at",
            "note",
        )
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }


class HomePageForm(forms.ModelForm):
    class Meta:
        model = HomePage
        fields = (
            "slug",
            "title",
            "is_active",
        )


class HomeBlockForm(forms.ModelForm):
    items = forms.JSONField(required=False)
    extra = forms.JSONField(required=False)

    class Meta:
        model = HomeBlock
        fields = (
            "type",
            "order",
            "is_active",
            "badge",
            "title",
            "subtitle",
            "body",
            "primary_button_text",
            "primary_button_url",
            "secondary_button_text",
            "secondary_button_url",
            "image",
            "items",
            "extra",
        )
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }
