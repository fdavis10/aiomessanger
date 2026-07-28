from __future__ import annotations

import logging
import mimetypes
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.crypto.services import get_message_crypto

from .models import Attachment, Chat, Message
from .pagination import chat_aad, touch_chat

User = get_user_model()
logger = logging.getLogger(__name__)

# Cap upload size to limit memory/disk DoS from a single request.
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024


def _guess_message_content_type(mime: str) -> str:
    if mime.startswith("image/"):
        return Message.ContentType.IMAGE
    if mime.startswith("video/"):
        return Message.ContentType.VIDEO
    return Message.ContentType.FILE


class AttachmentService:
    @staticmethod
    @transaction.atomic
    def create_from_upload(
        *,
        chat: Chat,
        sender: User,
        upload: UploadedFile,
        caption: str = "",
    ) -> Message:
        size = upload.size or 0
        if size <= 0:
            raise ValueError("Empty file")
        if size > MAX_ATTACHMENT_BYTES:
            raise ValueError(
                f"File too large (max {MAX_ATTACHMENT_BYTES // (1024 * 1024)} MB)"
            )

        raw = upload.read()
        # Do not log filename/content — only size for ops visibility.
        logger.info("Encrypting attachment upload size_bytes=%s", len(raw))

        mime = upload.content_type or mimetypes.guess_type(upload.name or "")[0] or ""
        filename = (upload.name or "file")[:255]
        content_type = _guess_message_content_type(mime)
        body = (caption or "").strip() or filename

        crypto = get_message_crypto()
        aad = chat_aad(chat.pk)
        file_ciphertext, file_nonce = crypto.encrypt(raw, associated_data=aad)
        text_ciphertext, text_nonce = crypto.encrypt_text(body, associated_data=aad)

        rel_path = Path("attachments") / f"{uuid.uuid4().hex}.bin"
        abs_path = Path(settings.MEDIA_ROOT) / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(file_ciphertext)

        message = Message.objects.create(
            chat=chat,
            sender=sender,
            ciphertext=text_ciphertext,
            nonce=bytes(text_nonce),
            content_type=content_type,
        )
        Attachment.objects.create(
            message=message,
            storage_path=str(rel_path).replace("\\", "/"),
            nonce=bytes(file_nonce),
            mime_type=mime[:128],
            size_bytes=len(raw),
            original_filename=filename,
        )
        touch_chat(chat)

        message = (
            Message.objects.select_related("sender", "attachment")
            .get(pk=message.pk)
        )
        from .realtime import broadcast_to_chat
        from .serializers import MessageSerializer

        broadcast_to_chat(
            chat_id=chat.pk,
            event_type="message.new",
            payload=MessageSerializer(message).data,
        )
        return message

    @staticmethod
    def read_decrypted(*, attachment: Attachment) -> bytes:
        path = Path(settings.MEDIA_ROOT) / attachment.storage_path
        if not path.is_file():
            raise FileNotFoundError("Attachment blob missing")
        crypto = get_message_crypto()
        return crypto.decrypt(
            path.read_bytes(),
            bytes(attachment.nonce),
            associated_data=chat_aad(attachment.message.chat_id),
        )

    @staticmethod
    def wipe_storage(*, attachment: Attachment) -> None:
        path = Path(settings.MEDIA_ROOT) / attachment.storage_path
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            logger.warning("Failed to wipe attachment file path=%s", attachment.pk)
