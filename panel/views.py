from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from chat.models import Message
from matchmaking.models import (
    HomeBlock,
    HomePage,
    Match,
    Swipe,
    UserBan,
    UserBlock,
    UserRecommendation,
    UserReport,
)
from profiles.models import (
    Profile,
    ProfilePhoto,
    QuestionnaireChoice,
    QuestionnaireQuestion,
    QuestionnaireSection,
)
from profiles.questionnaire import get_questionnaire_spec_for_profile, questionnaire_progress

from .forms import (
    HomeBlockForm,
    HomePageForm,
    ProfileEditForm,
    QuestionnaireChoiceForm,
    QuestionnaireQuestionForm,
    QuestionnaireSectionForm,
    UserBanForm,
    UserBanForUserForm,
    UserEditForm,
    UserSetPasswordForm,
)
from .models import AdminNotification


def staff_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def _paginate(request, qs, per_page: int = 50):
    paginator = Paginator(qs, per_page)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if "page" in params:
        params.pop("page")
    base_qs = params.urlencode()
    return page_obj, base_qs


@staff_required
def home_pages(request):
    qs = HomePage.objects.all().order_by("slug", "id")
    page_obj, base_qs = _paginate(request, qs, per_page=100)
    return render(
        request,
        "panel/home_pages_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
        },
    )


@staff_required
def home_page_create(request):
    if request.method == "POST":
        form = HomePageForm(request.POST)
        if form.is_valid():
            page = form.save()
            messages.success(request, "Страница создана")
            return redirect("panel_home_page_edit", page_id=page.id)
    else:
        form = HomePageForm()

    return render(
        request,
        "panel/home_page_form.html",
        {
            "form": form,
            "page": None,
            "blocks": [],
            "back_url": redirect("panel_home_pages").url,
        },
    )


@staff_required
def home_page_edit(request, page_id: int):
    page = get_object_or_404(HomePage, id=page_id)

    if request.method == "POST":
        form = HomePageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, "Страница сохранена")
            return redirect("panel_home_page_edit", page_id=page.id)
    else:
        form = HomePageForm(instance=page)

    blocks = page.blocks.all().order_by("order", "id")
    return render(
        request,
        "panel/home_page_form.html",
        {
            "form": form,
            "page": page,
            "blocks": blocks,
            "back_url": redirect("panel_home_pages").url,
        },
    )


@staff_required
def home_block_create(request, page_id: int):
    page = get_object_or_404(HomePage, id=page_id)

    if request.method == "POST":
        form = HomeBlockForm(request.POST, request.FILES)
        if form.is_valid():
            block = form.save(commit=False)
            block.page = page
            block.save()
            messages.success(request, "Блок создан")
            return redirect("panel_home_block_edit", block_id=block.id)
    else:
        form = HomeBlockForm()

    return render(
        request,
        "panel/home_block_form.html",
        {
            "form": form,
            "page": page,
            "block": None,
            "back_url": redirect("panel_home_page_edit", page_id=page.id).url,
        },
    )


@staff_required
def home_block_edit(request, block_id: int):
    block = get_object_or_404(HomeBlock.objects.select_related("page"), id=block_id)
    page = block.page

    if request.method == "POST":
        form = HomeBlockForm(request.POST, request.FILES, instance=block)
        if form.is_valid():
            form.save()
            messages.success(request, "Блок сохранён")
            return redirect("panel_home_block_edit", block_id=block.id)
    else:
        form = HomeBlockForm(instance=block)

    return render(
        request,
        "panel/home_block_form.html",
        {
            "form": form,
            "page": page,
            "block": block,
            "back_url": redirect("panel_home_page_edit", page_id=page.id).url,
        },
    )


@staff_required
def home_block_delete(request, block_id: int):
    if request.method != "POST":
        raise Http404

    block = get_object_or_404(HomeBlock, id=block_id)
    page_id = block.page_id
    block.delete()
    messages.success(request, "Блок удалён")
    return redirect("panel_home_page_edit", page_id=page_id)


@staff_required
def dashboard(request):
    users_count = User.objects.count()
    active_users_count = User.objects.filter(is_active=True).count()
    profiles_count = Profile.objects.count()
    photos_count = ProfilePhoto.objects.count()
    swipes_count = Swipe.objects.count()
    matches_count = Match.objects.count()
    messages_count = Message.objects.count()
    blocks_count = UserBlock.objects.count()
    reports_count = UserReport.objects.count()
    unresolved_reports_count = UserReport.objects.filter(resolved=False).count()
    bans_count = UserBan.objects.count()
    active_bans_count = UserBan.objects.active().count()

    recent_users = User.objects.order_by("-date_joined")[:8]
    recent_matches = Match.objects.select_related("user1", "user2").order_by("-created_at")[:8]

    notifications_count = AdminNotification.objects.count()
    notifications = AdminNotification.objects.select_related("user")[:12]

    return render(
        request,
        "panel/dashboard.html",
        {
            "users_count": users_count,
            "active_users_count": active_users_count,
            "profiles_count": profiles_count,
            "photos_count": photos_count,
            "swipes_count": swipes_count,
            "matches_count": matches_count,
            "messages_count": messages_count,
            "blocks_count": blocks_count,
            "reports_count": reports_count,
            "unresolved_reports_count": unresolved_reports_count,
            "bans_count": bans_count,
            "active_bans_count": active_bans_count,
            "recent_users": recent_users,
            "recent_matches": recent_matches,
            "notifications_count": notifications_count,
            "notifications": notifications,
        },
    )


@staff_required
def users_list(request):
    q = (request.GET.get("q") or "").strip()
    only_staff = request.GET.get("staff") == "1"
    only_inactive = request.GET.get("inactive") == "1"

    qs = User.objects.all().order_by("-date_joined")
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
    if only_staff:
        qs = qs.filter(is_staff=True)
    if only_inactive:
        qs = qs.filter(is_active=False)

    page_obj, base_qs = _paginate(request, qs, per_page=50)
    return render(
        request,
        "panel/users_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
            "only_staff": only_staff,
            "only_inactive": only_inactive,
        },
    )


@staff_required
def user_detail(request, user_id: int):
    u = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=u, actor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Пользователь сохранён")
            return redirect("panel_user_detail", user_id=u.id)
    else:
        form = UserEditForm(instance=u, actor=request.user)

    profile = getattr(u, "profile", None)

    swipes_made = Swipe.objects.filter(from_user=u).count()
    swipes_received = Swipe.objects.filter(to_user=u).count()
    matches = Match.objects.filter(Q(user1=u) | Q(user2=u)).count()
    messages_sent = Message.objects.filter(sender=u).count()
    blocks_made = UserBlock.objects.filter(blocker=u).count()
    blocks_received = UserBlock.objects.filter(blocked=u).count()
    reports_made = UserReport.objects.filter(reporter=u).count()
    reports_received = UserReport.objects.filter(reported_user=u).count()
    unresolved_reports_received = UserReport.objects.filter(reported_user=u, resolved=False).count()
    active_ban = UserBan.objects.active().filter(user=u).order_by("-created_at").first()

    return render(
        request,
        "panel/user_detail.html",
        {
            "target_user": u,
            "form": form,
            "profile": profile,
            "swipes_made": swipes_made,
            "swipes_received": swipes_received,
            "matches": matches,
            "messages_sent": messages_sent,
            "blocks_made": blocks_made,
            "blocks_received": blocks_received,
            "reports_made": reports_made,
            "reports_received": reports_received,
            "unresolved_reports_received": unresolved_reports_received,
            "active_ban": active_ban,
        },
    )


@staff_required
def user_compatibility_report(request, user_id: int, other_user_id: int):
    user_a = get_object_or_404(User, id=user_id)
    user_b = get_object_or_404(User, id=other_user_id)

    profile_a = getattr(user_a, "profile", None)
    profile_b = getattr(user_b, "profile", None)
    if profile_a is None or profile_b is None:
        raise Http404

    from matchmaking.compatibility import compatibility_breakdown

    report = compatibility_breakdown(profile_a, profile_b)

    def _label_value(value, choices_map: dict):
        if value is None:
            return "—"
        if isinstance(value, (list, tuple, set)):
            parts = []
            for item in value:
                item_s = str(item)
                parts.append(str(choices_map.get(item_s, item_s)))
            return ", ".join(parts) if parts else "—"
        value_s = str(value)
        return str(choices_map.get(value_s, value_s))

    sections = report.get("sections") or []
    for section in sections:
        for q in section.get("questions") or []:
            choices_map = {str(v): str(lbl) for v, lbl in (q.get("choices") or [])}
            for key in ("a_to_b", "b_to_a"):
                part = q.get(key)
                if not part:
                    continue
                part["score_percent"] = int(round(float(part.get("score") or 0.0) * 100))
                part["expected_label"] = _label_value(part.get("expected"), choices_map)
                part["actual_label"] = _label_value(part.get("actual"), choices_map)

    chart_labels = [s.get("title") or s.get("id") or "" for s in sections]
    chart_values_a_to_b = [s.get("a_to_b") for s in sections]
    chart_values_b_to_a = [s.get("b_to_a") for s in sections]

    return render(
        request,
        "panel/user_compatibility_report.html",
        {
            "user_a": user_a,
            "user_b": user_b,
            "profile_a": profile_a,
            "profile_b": profile_b,
            "report": report,
            "sections": sections,
            "chart_labels": chart_labels,
            "chart_values_a_to_b": chart_values_a_to_b,
            "chart_values_b_to_a": chart_values_b_to_a,
        },
    )


@staff_required
def user_recommendations(request, user_id: int):
    target_user = get_object_or_404(User, id=user_id)
    target_profile = getattr(target_user, "profile", None)
    if target_profile is None:
        raise Http404

    q = (request.GET.get("q") or "").strip()
    only_new = request.GET.get("only_new") == "1"
    raw_min_score = (request.GET.get("min_score") or "").strip()
    min_score = None
    if raw_min_score.isdigit():
        min_score = int(raw_min_score)

    qs = (
        Profile.objects.select_related("user")
        .filter(user__is_active=True)
        .exclude(user=target_user)
        .order_by("-updated_at")
    )

    swiped_to_ids = set(
        Swipe.objects.filter(from_user=target_user).values_list("to_user_id", flat=True)
    )
    if swiped_to_ids:
        qs = qs.exclude(user_id__in=swiped_to_ids)

    if q:
        qs = qs.filter(
            Q(user__username__icontains=q)
            | Q(display_name__icontains=q)
            | Q(city__icontains=q)
        )

    my_gender = target_profile.gender or None
    if target_profile.looking_for:
        if target_profile.looking_for == Profile.LookingFor.MEN:
            qs = qs.filter(gender=Profile.Gender.MALE)
        elif target_profile.looking_for == Profile.LookingFor.WOMEN:
            qs = qs.filter(gender=Profile.Gender.FEMALE)

    if my_gender == Profile.Gender.MALE:
        qs = qs.filter(
            Q(looking_for="")
            | Q(looking_for=Profile.LookingFor.EVERYONE)
            | Q(looking_for=Profile.LookingFor.MEN)
        )
    elif my_gender == Profile.Gender.FEMALE:
        qs = qs.filter(
            Q(looking_for="")
            | Q(looking_for=Profile.LookingFor.EVERYONE)
            | Q(looking_for=Profile.LookingFor.WOMEN)
        )
    elif my_gender:
        qs = qs.filter(Q(looking_for="") | Q(looking_for=Profile.LookingFor.EVERYONE))

    banned_ids = set(UserBan.objects.active().values_list("user_id", flat=True))
    if banned_ids:
        qs = qs.exclude(user_id__in=banned_ids)

    blocked_ids = set(
        UserBlock.objects.filter(blocker=target_user).values_list("blocked_id", flat=True)
    )
    blocked_by_ids = set(
        UserBlock.objects.filter(blocked=target_user).values_list("blocker_id", flat=True)
    )
    exclude_ids = blocked_ids | blocked_by_ids
    if exclude_ids:
        qs = qs.exclude(user_id__in=exclude_ids)

    recommended_ids = set(
        UserRecommendation.objects.filter(to_user=target_user).values_list(
            "recommended_user_id", flat=True
        )
    )

    if only_new and recommended_ids:
        qs = qs.exclude(user_id__in=recommended_ids)

    from matchmaking.compatibility import (
        build_question_specs,
        compatibility as compute_compatibility,
        compatibility_breakdown,
    )
    from profiles.questionnaire import get_questionnaire_spec

    question_specs = build_question_specs()
    breakdown_spec = get_questionnaire_spec()

    rows = []
    for candidate_profile in qs:
        scores = compute_compatibility(target_profile, candidate_profile, question_specs)
        breakdown = compatibility_breakdown(target_profile, candidate_profile, spec=breakdown_spec)
        sections = breakdown.get("sections") or []
        section_rows = [
            {
                "id": s.get("id") or "",
                "title": s.get("title") or "",
                "overall": s.get("overall"),
                "a_to_b": s.get("a_to_b"),
                "b_to_a": s.get("b_to_a"),
                "a_compared": s.get("a_compared"),
                "b_compared": s.get("b_compared"),
            }
            for s in sections
        ]
        compared_total = int(scores.get("a_compared", 0) or 0) + int(scores.get("b_compared", 0) or 0)
        score = scores.get("overall")
        if min_score is not None:
            if score is None or score < min_score:
                continue
        rows.append(
            {
                "profile": candidate_profile,
                "user": candidate_profile.user,
                "score": score,
                "a_to_b": scores.get("a_to_b"),
                "b_to_a": scores.get("b_to_a"),
                "a_compared": scores.get("a_compared"),
                "b_compared": scores.get("b_compared"),
                "compared_total": compared_total,
                "already_recommended": candidate_profile.user_id in recommended_ids,
                "sections": section_rows,
            }
        )

    rows.sort(
        key=lambda r: (
            r["score"] is not None,
            r["score"] or -1,
            r["compared_total"],
            r["profile"].updated_at,
        ),
        reverse=True,
    )

    rows = rows[:60]

    return render(
        request,
        "panel/user_recommendations.html",
        {
            "target_user": target_user,
            "target_profile": target_profile,
            "rows": rows,
            "q": q,
            "only_new": only_new,
            "min_score": raw_min_score,
        },
    )


@staff_required
def user_recommend_send(request, user_id: int):
    if request.method != "POST":
        raise Http404

    target_user = get_object_or_404(User, id=user_id)
    target_profile = getattr(target_user, "profile", None)
    if target_profile is None:
        raise Http404

    raw_recommended_user_id = request.POST.get("recommended_user_id")
    if not raw_recommended_user_id or not str(raw_recommended_user_id).isdigit():
        raise Http404

    recommended_user = get_object_or_404(User, id=int(raw_recommended_user_id))
    if recommended_user.id == target_user.id:
        raise Http404

    if not recommended_user.is_active:
        raise Http404

    if UserBan.objects.active().filter(user=recommended_user).exists():
        raise Http404

    if UserBlock.objects.filter(
        Q(blocker=target_user, blocked=recommended_user)
        | Q(blocker=recommended_user, blocked=target_user)
    ).exists():
        raise Http404

    recommended_profile = getattr(recommended_user, "profile", None)
    if recommended_profile is None:
        raise Http404

    from matchmaking.compatibility import compatibility as compute_compatibility

    scores = compute_compatibility(target_profile, recommended_profile)
    score = scores.get("overall")

    note = (request.POST.get("note") or "").strip()

    UserRecommendation.objects.create(
        to_user=target_user,
        recommended_user=recommended_user,
        created_by=request.user,
        score=score,
        note=note,
    )

    messages.success(request, "Рекомендация отправлена")

    next_url = request.POST.get("next")
    if next_url and str(next_url).startswith("/"):
        return redirect(next_url)

    return redirect("panel_user_recommendations", user_id=target_user.id)


@staff_required
def reports_list(request):
    q = (request.GET.get("q") or "").strip()
    only_open = request.GET.get("open") == "1"

    qs = UserReport.objects.select_related(
        "reporter",
        "reported_user",
        "resolved_by",
        "reporter__profile",
        "reported_user__profile",
    ).order_by("-created_at")

    if q:
        qs = qs.filter(
            Q(reporter__username__icontains=q)
            | Q(reported_user__username__icontains=q)
            | Q(message__icontains=q)
            | Q(reason__icontains=q)
        )

    if only_open:
        qs = qs.filter(resolved=False)

    page_obj, base_qs = _paginate(request, qs, per_page=80)
    return render(
        request,
        "panel/reports_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
            "only_open": only_open,
        },
    )


@staff_required
def report_resolve(request, report_id: int):
    if request.method != "POST":
        raise Http404

    rep = get_object_or_404(UserReport, id=report_id)
    if not rep.resolved:
        rep.resolved = True
        rep.resolved_at = timezone.now()
        rep.resolved_by = request.user
        rep.save(update_fields=["resolved", "resolved_at", "resolved_by"])

    messages.success(request, "Жалоба закрыта")
    next_url = request.POST.get("next")
    if next_url and str(next_url).startswith("/"):
        return redirect(next_url)
    return redirect("panel_reports")


@staff_required
def blocks_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = UserBlock.objects.select_related(
        "blocker",
        "blocked",
        "blocker__profile",
        "blocked__profile",
    ).order_by("-created_at")

    if q:
        qs = qs.filter(
            Q(blocker__username__icontains=q)
            | Q(blocked__username__icontains=q)
        )

    page_obj, base_qs = _paginate(request, qs, per_page=80)
    return render(
        request,
        "panel/blocks_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
        },
    )


@staff_required
def block_delete(request, block_id: int):
    if request.method != "POST":
        raise Http404

    b = get_object_or_404(UserBlock, id=block_id)
    b.delete()
    messages.success(request, "Блокировка удалена")
    next_url = request.POST.get("next")
    if next_url and str(next_url).startswith("/"):
        return redirect(next_url)
    return redirect("panel_blocks")


@staff_required
def bans_list(request):
    q = (request.GET.get("q") or "").strip()
    only_active = request.GET.get("active") == "1"

    qs = UserBan.objects.select_related("user", "created_by", "revoked_by").order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(user__username__icontains=q)
            | Q(user__email__icontains=q)
            | Q(note__icontains=q)
            | Q(reason__icontains=q)
        )

    now = timezone.now()
    if only_active:
        qs = qs.filter(revoked_at__isnull=True).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))

    page_obj, base_qs = _paginate(request, qs, per_page=80)
    return render(
        request,
        "panel/bans_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
            "only_active": only_active,
            "now": now,
        },
    )


@staff_required
def ban_create(request):
    if request.method == "POST":
        form = UserBanForm(request.POST)
        if form.is_valid():
            ban = form.save(commit=False)
            if ban.user_id == request.user.id:
                messages.error(request, "Нельзя забанить самого себя")
                return redirect("panel_ban_create")

            UserBan.objects.active().filter(user_id=ban.user_id).update(
                revoked_at=timezone.now(),
                revoked_by=request.user,
            )

            ban.created_by = request.user
            ban.save()
            messages.success(request, "Пользователь забанен")
            return redirect("panel_bans")
    else:
        form = UserBanForm()

    return render(
        request,
        "panel/ban_form.html",
        {
            "form": form,
            "back_url": redirect("panel_bans").url,
            "user_fixed": None,
        },
    )


@staff_required
def user_ban(request, user_id: int):
    u = get_object_or_404(User, id=user_id)
    if u.id == request.user.id:
        messages.error(request, "Нельзя забанить самого себя")
        return redirect("panel_user_detail", user_id=u.id)

    if request.method == "POST":
        form = UserBanForUserForm(request.POST)
        if form.is_valid():
            UserBan.objects.active().filter(user=u).update(
                revoked_at=timezone.now(),
                revoked_by=request.user,
            )

            ban = form.save(commit=False)
            ban.user = u
            ban.created_by = request.user
            ban.save()
            messages.success(request, "Пользователь забанен")
            return redirect("panel_user_detail", user_id=u.id)
    else:
        form = UserBanForUserForm()

    return render(
        request,
        "panel/ban_form.html",
        {
            "form": form,
            "back_url": redirect("panel_user_detail", user_id=u.id).url,
            "user_fixed": u,
        },
    )


@staff_required
def ban_revoke(request, ban_id: int):
    if request.method != "POST":
        raise Http404

    b = get_object_or_404(UserBan, id=ban_id)
    if b.revoked_at is None:
        b.revoked_at = timezone.now()
        b.revoked_by = request.user
        b.save(update_fields=["revoked_at", "revoked_by"])

    messages.success(request, "Бан снят")
    next_url = request.POST.get("next")
    if next_url and str(next_url).startswith("/"):
        return redirect(next_url)
    return redirect("panel_bans")


@staff_required
def user_set_password(request, user_id: int):
    u = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserSetPasswordForm(user=u, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Пароль обновлён")
            return redirect("panel_user_detail", user_id=u.id)
    else:
        form = UserSetPasswordForm(user=u)

    return render(
        request,
        "panel/user_set_password.html",
        {
            "target_user": u,
            "form": form,
        },
    )


@staff_required
def user_toggle_active(request, user_id: int):
    if request.method != "POST":
        raise Http404

    u = get_object_or_404(User, id=user_id)
    if u.id == request.user.id:
        messages.error(request, "Нельзя деактивировать самого себя")
        return redirect("panel_user_detail", user_id=u.id)

    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    messages.success(request, "Статус обновлён")
    return redirect("panel_user_detail", user_id=u.id)


@staff_required
def user_delete(request, user_id: int):
    u = get_object_or_404(User, id=user_id)

    if u.id == request.user.id:
        messages.error(request, "Нельзя удалить самого себя")
        return redirect("panel_user_detail", user_id=u.id)

    if (u.is_staff or u.is_superuser) and not request.user.is_superuser:
        messages.error(request, "Удалять staff/superuser может только суперпользователь")
        return redirect("panel_user_detail", user_id=u.id)

    profile = getattr(u, "profile", None)

    if request.method == "POST":
        if profile is not None:
            if profile.avatar:
                profile.avatar.delete(save=False)
            for p in profile.photos.all():
                if p.image:
                    p.image.delete(save=False)

        u.delete()
        messages.success(request, "Пользователь удалён")
        return redirect("panel_users")

    return render(
        request,
        "panel/user_delete_confirm.html",
        {
            "target_user": u,
            "profile": profile,
        },
    )


@staff_required
def profiles_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = Profile.objects.select_related("user").order_by("-updated_at")
    if q:
        qs = qs.filter(
            Q(user__username__icontains=q)
            | Q(display_name__icontains=q)
            | Q(city__icontains=q)
        )

    page_obj, base_qs = _paginate(request, qs, per_page=50)
    return render(
        request,
        "panel/profiles_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
        },
    )


@staff_required
def profile_detail(request, profile_id: int):
    profile = get_object_or_404(Profile, id=profile_id)

    spec_me = get_questionnaire_spec_for_profile(profile, "me")
    spec_ideal = get_questionnaire_spec_for_profile(profile, "ideal")

    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль сохранён")
            return redirect("panel_profile_detail", profile_id=profile.id)
    else:
        form = ProfileEditForm(instance=profile)

    me_answered, me_total, me_percent = questionnaire_progress(profile.questionnaire_me, spec_me)
    ideal_answered, ideal_total, ideal_percent = questionnaire_progress(profile.questionnaire_ideal, spec_ideal)

    def _answered(value) -> bool:
        if value is None:
            return False
        if isinstance(value, (list, tuple, set)):
            return any(str(x).strip() != "" for x in value if x is not None)
        return str(value).strip() != ""

    def _label_value(value, choices_map: dict) -> str:
        if not _answered(value):
            return "—"
        if isinstance(value, (list, tuple, set)):
            parts = []
            for item in value:
                item_s = str(item).strip()
                if item_s == "":
                    continue
                parts.append(str(choices_map.get(item_s, item_s)))
            return ", ".join(parts) if parts else "—"
        value_s = str(value).strip()
        return str(choices_map.get(value_s, value_s))

    questionnaire_sections = []
    me_answers = profile.questionnaire_me or {}
    ideal_answers = profile.questionnaire_ideal or {}
    for section in spec_me:
        rows = []
        for q in section["questions"]:
            choices_map = dict(q["choices"])
            qid = q["id"]

            me_value = me_answers.get(qid)
            ideal_value = ideal_answers.get(qid)

            me_answered_flag = _answered(me_value)
            ideal_answered_flag = _answered(ideal_value)

            me_label = _label_value(me_value, choices_map)
            ideal_label = _label_value(ideal_value, choices_map)

            rows.append(
                {
                    "id": qid,
                    "text": q["text"],
                    "me_answered": me_answered_flag,
                    "me_label": me_label,
                    "ideal_answered": ideal_answered_flag,
                    "ideal_label": ideal_label,
                }
            )
        questionnaire_sections.append(
            {
                "id": section["id"],
                "title": section["title"],
                "questions": rows,
            }
        )

    questionnaire_sections_ideal = []
    for section in spec_ideal:
        rows = []
        for q in section["questions"]:
            choices_map = dict(q["choices"])
            qid = q["id"]

            ideal_value = ideal_answers.get(qid)
            ideal_answered_flag = _answered(ideal_value)
            ideal_label = _label_value(ideal_value, choices_map)

            rows.append(
                {
                    "id": qid,
                    "text": q["text"],
                    "ideal_answered": ideal_answered_flag,
                    "ideal_label": ideal_label,
                }
            )
        questionnaire_sections_ideal.append(
            {
                "id": section["id"],
                "title": section["title"],
                "questions": rows,
            }
        )

    photos_qs = profile.photos.all()[:6]

    return render(
        request,
        "panel/profile_detail.html",
        {
            "profile": profile,
            "form": form,
            "me_answered": me_answered,
            "me_total": me_total,
            "me_percent": me_percent,
            "ideal_answered": ideal_answered,
            "ideal_total": ideal_total,
            "ideal_percent": ideal_percent,
            "photos": photos_qs,
            "questionnaire_sections": questionnaire_sections,
            "questionnaire_sections_ideal": questionnaire_sections_ideal,
        },
    )


@staff_required
def photos_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = ProfilePhoto.objects.select_related("profile", "profile__user").order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(profile__user__username__icontains=q)
            | Q(profile__display_name__icontains=q)
        )

    page_obj, base_qs = _paginate(request, qs, per_page=60)
    return render(
        request,
        "panel/photos_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
        },
    )


@staff_required
def photo_delete(request, photo_id: int):
    if request.method != "POST":
        raise Http404

    photo = get_object_or_404(ProfilePhoto, id=photo_id)
    if photo.image:
        photo.image.delete(save=False)
    photo.delete()
    messages.success(request, "Фото удалено")
    return redirect("panel_photos")


@staff_required
def swipes_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = Swipe.objects.select_related("from_user", "to_user").order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(from_user__username__icontains=q)
            | Q(to_user__username__icontains=q)
            | Q(value__icontains=q)
        )

    page_obj, base_qs = _paginate(request, qs, per_page=80)
    return render(
        request,
        "panel/swipes_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
        },
    )


@staff_required
def swipe_delete(request, swipe_id: int):
    if request.method != "POST":
        raise Http404

    swipe = get_object_or_404(Swipe, id=swipe_id)
    swipe.delete()
    messages.success(request, "Swipe удалён")
    return redirect("panel_swipes")


@staff_required
def matches_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = Match.objects.select_related("user1", "user2").order_by("-created_at")
    if q:
        qs = qs.filter(Q(user1__username__icontains=q) | Q(user2__username__icontains=q))

    page_obj, base_qs = _paginate(request, qs, per_page=80)
    return render(
        request,
        "panel/matches_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
        },
    )


@staff_required
def match_delete(request, match_id: int):
    if request.method != "POST":
        raise Http404

    match = get_object_or_404(Match, id=match_id)
    match.delete()
    messages.success(request, "Мэтч удалён")
    return redirect("panel_matches")


@staff_required
def messages_list(request):
    q = (request.GET.get("q") or "").strip()

    qs = Message.objects.select_related("match", "sender").order_by("-created_at")
    if q:
        qs = qs.filter(Q(sender__username__icontains=q) | Q(text__icontains=q))

    page_obj, base_qs = _paginate(request, qs, per_page=80)
    return render(
        request,
        "panel/messages_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
            "q": q,
        },
    )


@staff_required
def message_delete(request, message_id: int):
    if request.method != "POST":
        raise Http404

    msg = get_object_or_404(Message, id=message_id)
    msg.delete()
    messages.success(request, "Сообщение удалено")
    return redirect("panel_messages")


@staff_required
def questionnaire_sections(request):
    qs = QuestionnaireSection.objects.all().order_by("order", "id")
    page_obj, base_qs = _paginate(request, qs, per_page=100)
    return render(
        request,
        "panel/questionnaire_sections_list.html",
        {
            "page_obj": page_obj,
            "base_qs": base_qs,
        },
    )


@staff_required
def questionnaire_section_create(request):
    if request.method == "POST":
        form = QuestionnaireSectionForm(request.POST)
        if form.is_valid():
            section = form.save()
            messages.success(request, "Раздел создан")
            return redirect("panel_questionnaire_section_edit", section_id=section.id)
    else:
        form = QuestionnaireSectionForm()

    return render(
        request,
        "panel/questionnaire_section_form.html",
        {
            "form": form,
            "section": None,
            "questions": [],
            "back_url": redirect("panel_questionnaire_sections").url,
        },
    )


@staff_required
def questionnaire_section_edit(request, section_id: int):
    section = get_object_or_404(QuestionnaireSection, id=section_id)

    if request.method == "POST":
        form = QuestionnaireSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, "Раздел сохранён")
            return redirect("panel_questionnaire_section_edit", section_id=section.id)
    else:
        form = QuestionnaireSectionForm(instance=section)

    questions = section.questions.all().order_by("order", "id")
    return render(
        request,
        "panel/questionnaire_section_form.html",
        {
            "form": form,
            "section": section,
            "questions": questions,
            "back_url": redirect("panel_questionnaire_sections").url,
        },
    )


@staff_required
def questionnaire_section_delete(request, section_id: int):
    if request.method != "POST":
        raise Http404

    section = get_object_or_404(QuestionnaireSection, id=section_id)
    section.delete()
    messages.success(request, "Раздел удалён")
    return redirect("panel_questionnaire_sections")


@staff_required
def questionnaire_question_create(request, section_id: int):
    section = get_object_or_404(QuestionnaireSection, id=section_id)

    if request.method == "POST":
        form = QuestionnaireQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.section = section
            question.save()
            messages.success(request, "Вопрос создан")
            return redirect("panel_questionnaire_question_edit", question_id=question.id)
    else:
        form = QuestionnaireQuestionForm()

    return render(
        request,
        "panel/questionnaire_question_form.html",
        {
            "form": form,
            "section": section,
            "question": None,
            "choices": [],
            "back_url": redirect("panel_questionnaire_section_edit", section_id=section.id).url,
        },
    )


@staff_required
def questionnaire_question_edit(request, question_id: int):
    question = get_object_or_404(
        QuestionnaireQuestion.objects.select_related("section"),
        id=question_id,
    )

    if request.method == "POST":
        form = QuestionnaireQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Вопрос сохранён")
            return redirect("panel_questionnaire_question_edit", question_id=question.id)
    else:
        form = QuestionnaireQuestionForm(instance=question)

    choices = question.choices.all().order_by("order", "id")
    return render(
        request,
        "panel/questionnaire_question_form.html",
        {
            "form": form,
            "section": question.section,
            "question": question,
            "choices": choices,
            "back_url": redirect("panel_questionnaire_section_edit", section_id=question.section_id).url,
        },
    )


@staff_required
def questionnaire_question_delete(request, question_id: int):
    if request.method != "POST":
        raise Http404

    question = get_object_or_404(QuestionnaireQuestion, id=question_id)
    section_id = question.section_id
    question.delete()
    messages.success(request, "Вопрос удалён")
    return redirect("panel_questionnaire_section_edit", section_id=section_id)


@staff_required
def questionnaire_choice_create(request, question_id: int):
    question = get_object_or_404(
        QuestionnaireQuestion.objects.select_related("section"),
        id=question_id,
    )

    if request.method == "POST":
        form = QuestionnaireChoiceForm(request.POST)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.question = question
            choice.save()
            messages.success(request, "Ответ добавлен")
            return redirect("panel_questionnaire_question_edit", question_id=question.id)
    else:
        form = QuestionnaireChoiceForm()

    return render(
        request,
        "panel/questionnaire_choice_form.html",
        {
            "form": form,
            "section": question.section,
            "question": question,
            "choice": None,
            "back_url": redirect("panel_questionnaire_question_edit", question_id=question.id).url,
        },
    )


@staff_required
def questionnaire_choice_edit(request, choice_id: int):
    choice = get_object_or_404(
        QuestionnaireChoice.objects.select_related("question", "question__section"),
        id=choice_id,
    )

    if request.method == "POST":
        form = QuestionnaireChoiceForm(request.POST, instance=choice)
        if form.is_valid():
            form.save()
            messages.success(request, "Ответ сохранён")
            return redirect("panel_questionnaire_question_edit", question_id=choice.question_id)
    else:
        form = QuestionnaireChoiceForm(instance=choice)

    return render(
        request,
        "panel/questionnaire_choice_form.html",
        {
            "form": form,
            "section": choice.question.section,
            "question": choice.question,
            "choice": choice,
            "back_url": redirect("panel_questionnaire_question_edit", question_id=choice.question_id).url,
        },
    )


@staff_required
def questionnaire_choice_delete(request, choice_id: int):
    if request.method != "POST":
        raise Http404

    choice = get_object_or_404(QuestionnaireChoice, id=choice_id)
    question_id = choice.question_id
    choice.delete()
    messages.success(request, "Ответ удалён")
    return redirect("panel_questionnaire_question_edit", question_id=question_id)
