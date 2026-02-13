from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from matchmaking.models import UserBan, UserBlock

from .forms import OnboardingForm, PhotoUploadForm, QuestionnaireForm
from .models import Profile, ProfilePhoto
from .questionnaire import get_questionnaire_spec_for_profile, questionnaire_progress


@login_required
def onboarding(request):
    profile = request.user.profile

    if request.method == "POST":
        form = OnboardingForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("feed")
    else:
        form = OnboardingForm(instance=profile)

    return render(request, "profiles/onboarding.html", {"form": form})


@login_required
def me(request):
    profile = request.user.profile
    upload_form = PhotoUploadForm()

    spec_me = get_questionnaire_spec_for_profile(profile, "me")
    spec_ideal = get_questionnaire_spec_for_profile(profile, "ideal")
    me_answered, me_total, me_percent = questionnaire_progress(profile.questionnaire_me, spec_me)
    ideal_answered, ideal_total, ideal_percent = questionnaire_progress(profile.questionnaire_ideal, spec_ideal)
    blocks_count = UserBlock.objects.filter(blocker=request.user).count()
    return render(
        request,
        "profiles/me.html",
        {
            "profile": profile,
            "upload_form": upload_form,
            "q_me_answered": me_answered,
            "q_me_total": me_total,
            "q_me_percent": me_percent,
            "q_ideal_answered": ideal_answered,
            "q_ideal_total": ideal_total,
            "q_ideal_percent": ideal_percent,
            "blocks_count": blocks_count,
        },
    )


@login_required
def blocked_users(request):
    qs = (
        UserBlock.objects.filter(blocker=request.user)
        .select_related("blocked", "blocked__profile")
        .order_by("-created_at")
    )

    rows = []
    for b in qs:
        other = b.blocked
        other_profile = other.profile if hasattr(other, "profile") else None
        other_name = None
        if other_profile is not None:
            other_name = other_profile.display_name
        if not other_name:
            other_name = other.get_username()
        other_avatar_url = None
        if other_profile is not None and other_profile.avatar:
            other_avatar_url = other_profile.avatar.url
        rows.append({"block": b, "other": other, "other_name": other_name, "other_avatar_url": other_avatar_url})

    return render(request, "profiles/blocks.html", {"rows": rows})


@login_required
def questionnaire(request, kind: str):
    if kind not in ("me", "ideal"):
        raise Http404

    profile = request.user.profile

    spec = get_questionnaire_spec_for_profile(profile, kind)

    before_answers = profile.questionnaire_me if kind == "me" else profile.questionnaire_ideal
    _, _, before_percent = questionnaire_progress(before_answers, spec)

    if request.method == "POST":
        form = QuestionnaireForm(request.POST, profile=profile, kind=kind)
        if form.is_valid():
            form.save()

            after_answers = profile.questionnaire_me if kind == "me" else profile.questionnaire_ideal
            _, _, after_percent = questionnaire_progress(after_answers, spec)
            if before_percent < 100 and after_percent == 100:
                from panel.models import AdminNotification

                AdminNotification.objects.create(
                    event=AdminNotification.Event.QUESTIONNAIRE_COMPLETED,
                    user=request.user,
                    questionnaire_kind=kind,
                )

            return redirect("questionnaire", kind=kind)
    else:
        form = QuestionnaireForm(profile=profile, kind=kind)

    answers = profile.questionnaire_me if kind == "me" else profile.questionnaire_ideal
    answered, total, percent = questionnaire_progress(answers, spec)

    other_kind = "ideal" if kind == "me" else "me"
    other_answers = profile.questionnaire_ideal if kind == "me" else profile.questionnaire_me
    other_spec = get_questionnaire_spec_for_profile(profile, other_kind)
    other_answered, other_total, other_percent = questionnaire_progress(other_answers, other_spec)

    section_hints = {
        "principles": "Ценности и принципы, которые определяют поведение в отношениях и в жизни. Нужны, чтобы находить людей с похожими установками.",
        "housing": "Ожидания по быту и личному пространству. Нужны, чтобы снизить конфликтность в совместной жизни.",
        "roles": "Предпочтения по ролям и принятию решений в паре. Нужны, чтобы совпали ожидания от партнёрства.",
        "work": "Отношение к работе, карьере и балансу. Нужны, чтобы понимать темп жизни и приоритеты.",
        "wife_expenses": "Ожидания по финансам/подаркам/бюджету. Нужны, чтобы избежать разногласий по деньгам.",
        "sexual": "Комфорт и ожидания в интимной сфере. Нужны, чтобы оценить базовую совместимость.",
        "rest": "Как вы отдыхаете и проводите свободное время. Нужны, чтобы было легко планировать досуг вместе.",
        "love_language": "Как вы предпочитаете получать/давать любовь и заботу. Нужны, чтобы лучше понимать друг друга.",
        "tests": "Ситуационные вопросы для проверки реакций и границ. Нужны, чтобы увидеть поведение в стрессовых/неоднозначных ситуациях.",
    }

    sections = []
    for section in spec:
        sid = section["id"]
        rows = []
        for q in section["questions"]:
            qid = q["id"]
            rows.append(
                {
                    "id": qid,
                    "text": q["text"],
                    "input_type": (q.get("input_type") or "choice"),
                    "field": form[qid],
                    "is_multiple": bool(q.get("is_multiple")),
                }
            )
        sections.append(
            {
                "id": sid,
                "title": section["title"],
                "hint": section_hints.get(sid, ""),
                "questions": rows,
            }
        )

    return render(
        request,
        "profiles/questionnaire.html",
        {
            "form": form,
            "kind": kind,
            "sections": sections,
            "answered": answered,
            "total": total,
            "percent": percent,
            "other_kind": other_kind,
            "other_answered": other_answered,
            "other_total": other_total,
            "other_percent": other_percent,
        },
    )


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        form = OnboardingForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("me")
    else:
        form = OnboardingForm(instance=profile)

    return render(request, "profiles/edit.html", {"form": form})


@login_required
def upload_photo(request):
    profile = request.user.profile

    if request.method == "POST":
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.profile = profile
            photo.save()

    next_url = request.POST.get("next")
    if next_url and str(next_url).startswith("/"):
        return redirect(next_url)
    return redirect("me")


@login_required
def photos_manage(request):
    profile = request.user.profile
    upload_form = PhotoUploadForm()
    photos = profile.photos.all()
    return render(
        request,
        "profiles/photos_manage.html",
        {
            "profile": profile,
            "upload_form": upload_form,
            "photos": photos,
        },
    )


@login_required
def photo_delete(request, photo_id: int):
    if request.method != "POST":
        raise Http404

    profile = request.user.profile
    photo = get_object_or_404(ProfilePhoto, id=photo_id, profile=profile)
    if photo.image:
        photo.image.delete(save=False)
    photo.delete()
    return redirect("photos_manage")


@login_required
def photo_move(request, photo_id: int, direction: str):
    if request.method != "POST":
        raise Http404

    if direction not in ("up", "down"):
        raise Http404

    profile = request.user.profile
    photo = get_object_or_404(ProfilePhoto, id=photo_id, profile=profile)

    qs = profile.photos.all().order_by("order", "created_at", "id")
    ids = list(qs.values_list("id", flat=True))
    try:
        idx = ids.index(photo.id)
    except ValueError:
        return redirect("photos_manage")

    if direction == "up" and idx > 0:
        swap_id = ids[idx - 1]
    elif direction == "down" and idx < len(ids) - 1:
        swap_id = ids[idx + 1]
    else:
        return redirect("photos_manage")

    other = get_object_or_404(ProfilePhoto, id=swap_id, profile=profile)
    photo.order, other.order = other.order, photo.order
    photo.save(update_fields=["order"])
    other.save(update_fields=["order"])
    return redirect("photos_manage")


@login_required
def photo_set_avatar(request, photo_id: int):
    if request.method != "POST":
        raise Http404

    profile = request.user.profile
    photo = get_object_or_404(ProfilePhoto, id=photo_id, profile=profile)
    if photo.image:
        profile.avatar = photo.image
        profile.save(update_fields=["avatar", "updated_at"])
    return redirect("photos_manage")


def public_profile(request, user_id: int):
    profile = get_object_or_404(Profile, user_id=user_id)

    if not profile.user.is_active:
        raise Http404

    if UserBan.objects.active().filter(user=profile.user).exists():
        raise Http404

    i_blocked = False
    blocked_by_other = False
    if request.user.is_authenticated and request.user.id != profile.user_id:
        i_blocked = UserBlock.objects.filter(blocker=request.user, blocked_id=profile.user_id).exists()
        blocked_by_other = UserBlock.objects.filter(blocker_id=profile.user_id, blocked=request.user).exists()
        if blocked_by_other:
            raise Http404

    return render(
        request,
        "profiles/public.html",
        {
            "profile": profile,
            "i_blocked": i_blocked,
        },
    )
