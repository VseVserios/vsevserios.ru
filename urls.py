from django.urls import path

from .views import inbox, messages_partial, room, send_message, send_newsletter

urlpatterns = [
    path("", inbox, name="chat_inbox"),
    path("<int:match_id>/", room, name="chat_room"),
    path("<int:match_id>/messages/", messages_partial, name="chat_messages"),
    path("<int:match_id>/send/", send_message, name="chat_send"),
    path("newsletter/send/", send_newsletter, name="chat_send_newsletter"),
]
