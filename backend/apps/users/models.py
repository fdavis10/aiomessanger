from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user: profile fields for messenger presence/UX.

    Authentication still uses Django's password hashers (Argon2 preferred).
    Message content encryption is a separate concern (MessageCrypto).
    """

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        help_text=_("Public profile avatar."),
    )
    banner_image = models.ImageField(
        upload_to="banners/",
        blank=True,
        null=True,
        help_text=_("Custom profile banner image."),
    )
    banner_style = models.JSONField(
        blank=True,
        null=True,
        help_text=_("Generated banner: {from, to, motifs[]}."),
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text=_("Phone number shown on the public profile card."),
    )
    bio = models.CharField(max_length=255, blank=True, default="")
    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Last activity timestamp for presence UI."),
    )

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        return self.username
