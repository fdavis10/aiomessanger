from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttachmentDownloadView,
    AttachmentUploadView,
    ChatMembersView,
    ChatViewSet,
    MessageViewSet,
)

router = DefaultRouter()
router.register(r"chats", ChatViewSet, basename="chat")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "chats/<uuid:chat_id>/members/",
        ChatMembersView.as_view(),
        name="chat-members",
    ),
    path(
        "chats/<uuid:chat_id>/messages/",
        MessageViewSet.as_view({"get": "list", "post": "create"}),
        name="chat-messages",
    ),
    path(
        "chats/<uuid:chat_id>/messages/<uuid:pk>/",
        MessageViewSet.as_view({"delete": "destroy"}),
        name="chat-message-detail",
    ),
    path(
        "chats/<uuid:chat_id>/attachments/",
        AttachmentUploadView.as_view(),
        name="chat-attachments",
    ),
    path(
        "attachments/<uuid:attachment_id>/download/",
        AttachmentDownloadView.as_view(),
        name="attachment-download",
    ),
]
