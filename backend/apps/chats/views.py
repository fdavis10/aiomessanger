from __future__ import annotations

from django.http import FileResponse, Http404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .attachments import AttachmentService
from .drf_permissions import IsChatMember
from .models import Attachment, Chat, ChatMember, Message
from .pagination import ChatCursorPagination, MessageCursorPagination
from .serializers import (
    AttachmentUploadSerializer,
    ChatCreateSerializer,
    ChatMemberSerializer,
    ChatSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)
from .services import MessageService, get_chat_for_member


class ChatViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, IsChatMember]
    pagination_class = ChatCursorPagination

    def get_queryset(self):
        return (
            Chat.objects.filter(memberships__user=self.request.user)
            .prefetch_related("memberships__user")
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ChatCreateSerializer
        return ChatSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()
        out = ChatSerializer(chat, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)


class ChatMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        try:
            chat = get_chat_for_member(chat_id=chat_id, user=request.user)
        except Http404 as exc:
            raise NotFound() from exc
        memberships = chat.memberships.select_related("user").all()
        return Response(ChatMemberSerializer(memberships, many=True).data)


class MessageViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    pagination_class = MessageCursorPagination
    serializer_class = MessageSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        try:
            self.chat = get_chat_for_member(
                chat_id=self.kwargs["chat_id"], user=request.user
            )
        except Http404 as exc:
            raise NotFound() from exc

    def get_queryset(self):
        return (
            Message.objects.filter(chat=self.chat)
            .select_related("sender", "attachment")
            .order_by("-created_at", "-id")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["chat"] = getattr(self, "chat", None)
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        out = MessageSerializer(message, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        try:
            MessageService.soft_delete(message=message, actor=request.user)
        except PermissionError as exc:
            raise PermissionDenied(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttachmentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "uploads"

    def post(self, request, chat_id):
        try:
            chat = get_chat_for_member(chat_id=chat_id, user=request.user)
        except Http404 as exc:
            raise NotFound() from exc

        serializer = AttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message = AttachmentService.create_from_upload(
                chat=chat,
                sender=request.user,
                upload=serializer.validated_data["file"],
                caption=serializer.validated_data.get("caption") or "",
            )
        except ValueError as exc:
            raise ValidationError({"file": str(exc)}) from exc

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class AttachmentDownloadView(APIView):
    """Decrypt and stream attachment — members only; never expose raw ciphertext URL."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "uploads"

    def get(self, request, attachment_id):
        attachment = (
            Attachment.objects.select_related("message__chat")
            .filter(pk=attachment_id)
            .first()
        )
        if attachment is None:
            raise NotFound()
        if not ChatMember.objects.filter(
            chat_id=attachment.message.chat_id, user=request.user
        ).exists():
            raise NotFound()
        if attachment.message.is_deleted:
            raise NotFound()

        try:
            payload = AttachmentService.read_decrypted(attachment=attachment)
        except (FileNotFoundError, Exception):
            raise NotFound() from None

        from io import BytesIO

        response = FileResponse(
            BytesIO(payload),
            as_attachment=True,
            filename=attachment.original_filename,
        )
        if attachment.mime_type:
            response["Content-Type"] = attachment.mime_type
        response["X-Content-Type-Options"] = "nosniff"
        return response
