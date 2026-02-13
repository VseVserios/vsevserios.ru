from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from matchmaking.models import Match
from matchmaking.models import UserBan, UserBlock

from .forms import MessageForm
from .models import Message


def _user_is_in_match(match: Match, user) -> bool:
    # Администраторы могут писать в администраторские чаты
    if user.is_superuser and match.is_admin_chat:
        return True
    
    if user.id not in (match.user1_id, match.user2_id):
        return False

    if not match.user1.is_active or not match.user2.is_active:
        return False

    if UserBan.objects.active().filter(user_id__in=[match.user1_id, match.user2_id]).exists():
        return False

    if UserBlock.objects.filter(
        Q(blocker_id=match.user1_id, blocked_id=match.user2_id)
        | Q(blocker_id=match.user2_id, blocked_id=match.user1_id)
    ).exists():
        return False

    return True


@login_required
def inbox(request):
    blocked_ids = set(
        UserBlock.objects.filter(blocker=request.user).values_list("blocked_id", flat=True)
    )
    blocked_by_ids = set(
        UserBlock.objects.filter(blocked=request.user).values_list("blocker_id", flat=True)
    )

    # Для администраторов показываем ВСЕ административные чаты (всех пользователей)
    if request.user.is_superuser:
        qs = (
            Match.objects.filter(is_admin_chat=True)
            .select_related(
                "user1",
                "user2",
                "user1__profile",
                "user2__profile",
            )
            .prefetch_related("messages")
            .order_by("-created_at")
        )
    else:
        qs = (
            Match.objects.filter(Q(user1=request.user) | Q(user2=request.user))
            .select_related(
                "user1",
                "user2",
                "user1__profile",
                "user2__profile",
            )
            .prefetch_related("messages")
            .order_by("-created_at")
        )

    rows = []
    for m in qs:
        # Для административных чатов "другой" это всегда обычный пользователь
        if m.is_admin_chat:
            other = m.user1 if m.user2.is_superuser else m.user2
        else:
            other = m.other(request.user)
        
        if not other.is_active:
            continue
        if UserBan.objects.active().filter(user=other).exists():
            continue
        if other.id in blocked_ids or other.id in blocked_by_ids:
            continue

        other_profile = other.profile if hasattr(other, "profile") else None

        other_name = None
        if other_profile is not None:
            other_name = other_profile.display_name
        if not other_name:
            other_name = other.get_username()

        other_avatar_url = None
        if other_profile is not None and other_profile.avatar:
            other_avatar_url = other_profile.avatar.url

        last_message = m.messages.order_by("-created_at").first()
        last_message_text = ""
        last_message_time = None
        if last_message:
            last_message_text = (last_message.text or "")[:100]
            last_message_time = last_message.created_at

        rows.append(
            {
                "match": m,
                "other": other,
                "other_name": other_name,
                "other_avatar_url": other_avatar_url,
                "last_message_text": last_message_text,
                "last_message_time": last_message_time,
            }
        )

    return render(request, "chat/inbox.html", {"rows": rows})


@login_required
def room(request, match_id: int):
    match = get_object_or_404(Match.objects.select_related("user1", "user2"), id=match_id)

    if not _user_is_in_match(match, request.user):
        raise Http404

    other = match.other(request.user)
    other_profile = other.profile if hasattr(other, "profile") else None
    other_name = None
    if other_profile is not None:
        other_name = other_profile.display_name
    if not other_name:
        other_name = other.get_username()
    form = MessageForm()

    return render(
        request,
        "chat/room.html",
        {
            "match": match,
            "other": other,
            "other_name": other_name,
            "form": form,
        },
    )


@login_required
def messages_partial(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)

    if not _user_is_in_match(match, request.user):
        raise Http404

    qs = Message.objects.filter(match=match).select_related("sender")
    return render(request, "chat/_messages.html", {"match": match, "messages": qs})


@login_required
def send_message(request, match_id: int):
    if request.method != "POST":
        raise Http404

    match = get_object_or_404(Match, id=match_id)

    if not _user_is_in_match(match, request.user):
        raise Http404

    form = MessageForm(request.POST)
    if form.is_valid():
        msg = form.save(commit=False)
        msg.match = match
        msg.sender = request.user
        msg.save()

        recipient = match.other(request.user)
        if recipient is not None and recipient.is_active:
            from accounts.models import UserNotification
            from accounts.notifications import create_user_notification

            sender_profile = getattr(request.user, "profile", None)
            sender_name = None
            if sender_profile is not None:
                sender_name = sender_profile.display_name
            if not sender_name:
                sender_name = request.user.get_username()

            text_preview = (msg.text or "").strip()
            if len(text_preview) > 120:
                text_preview = text_preview[:120] + "…"

            create_user_notification(
                recipient=recipient,
                event=UserNotification.Event.NEW_MESSAGE,
                title=f"Сообщение от {sender_name}",
                body=text_preview,
                url=f"/chat/{match.id}/",
            )

    if request.headers.get("HX-Request") == "true":
        qs = Message.objects.filter(match=match).select_related("sender")
        return render(request, "chat/_messages.html", {"match": match, "messages": qs})

    return redirect("chat_room", match_id=match_id)


@login_required
def send_newsletter(request):
    """Отправляет рассылку сообщения от администратора всем пользователям"""
    if not request.user.is_superuser:
        raise Http404

    if request.method != "POST":
        raise Http404

    message_text = request.POST.get("message_text", "").strip()
    if not message_text:
        print("[NEWSLETTER] Пустое сообщение!")
        return redirect("chat_inbox")
    
    print(f"[NEWSLETTER] Начало отправки рассылки от {request.user.username}: {message_text[:50]}")

    from django.contrib.auth import get_user_model

    User = get_user_model()
    users = User.objects.filter(is_superuser=False, is_active=True)
    sent_count = 0

    for user in users:
        # Найти административный чат с этим пользователем
        match = Match.objects.filter(
            is_admin_chat=True
        ).filter(
            Q(user1=request.user, user2=user) |
            Q(user1=user, user2=request.user)
        ).first()
        
        if not match:
            print(f"[NEWSLETTER] Чат не найден для пользователя {user.username}")
            continue
        
        msg = Message.objects.create(
            match=match,
            sender=request.user,
            text=message_text,
        )
        sent_count += 1
        print(f"[NEWSLETTER] Сообщение {msg.id} отправлено пользователю {user.username}")
        
        # Отправить уведомление пользователю
        try:
            from accounts.models import UserNotification
            from accounts.notifications import create_user_notification
            
            create_user_notification(
                recipient=user,
                event=UserNotification.Event.NEW_MESSAGE,
                title="📢 Рассылка от администратора",
                body=message_text[:120] + "..." if len(message_text) > 120 else message_text,
                url=f"/chat/{match.id}/",
            )
        except Exception as e:
            print(f"[NEWSLETTER] Ошибка при отправке уведомления: {e}")
    
    print(f"[NEWSLETTER] Рассылка завершена: {sent_count} сообщений отправлено")

    return redirect("chat_inbox")
