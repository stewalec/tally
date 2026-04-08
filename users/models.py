import random
import re
import string
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

import phonenumbers


def generate_username(first_name: str, last_name: str) -> str:
    """Generate a lowercase username from first + last name (letters/numbers only)."""
    raw = f"{first_name}{last_name}".lower()
    return re.sub(r"[^a-z0-9]", "", raw)


def normalize_phone(raw: str) -> str | None:
    """Normalize a phone number string to E.164 format (e.g. +12125551234)."""
    try:
        parsed = phonenumbers.parse(raw, "US")
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None


class TallyUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        normalized = normalize_phone(phone_number)
        if not normalized:
            raise ValueError(f"Invalid phone number: {phone_number}")
        user = self.model(phone_number=normalized, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        user = self.create_user(phone_number, password, **extra_fields)
        if password:
            user.set_password(password)
            user.save(using=self._db)
        return user


class TallyUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.SlugField(max_length=100, unique=True, default="", help_text="URL-friendly name (auto-generated from first + last name)")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = TallyUserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def save(self, *args, **kwargs):
        if not self.username:
            base = generate_username(self.first_name, self.last_name) or "user"
            candidate = base
            counter = 1
            while TallyUser.objects.filter(username=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}{counter}"
                counter += 1
            self.username = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        full = self.get_full_name()
        return full if full else self.phone_number

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.phone_number

    def get_short_name(self):
        return self.first_name or self.phone_number

    @property
    def display_name(self):
        return self.get_full_name() or self.phone_number

    @property
    def masked_phone(self):
        if len(self.phone_number) >= 4:
            return "•••" + self.phone_number[-4:]
        return self.phone_number


class OTPCode(models.Model):
    user = models.ForeignKey(TallyUser, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "OTP Code"
        verbose_name_plural = "OTP Codes"

    def __str__(self):
        return f"OTP for {self.user} (used={self.used})"

    @property
    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()

    @classmethod
    def generate_for(cls, user) -> "OTPCode":
        from django.conf import settings

        # Invalidate any existing unused codes
        cls.objects.filter(user=user, used=False).update(used=True)

        code = "".join(random.choices(string.digits, k=6))
        expiry_minutes = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        return cls.objects.create(user=user, code=code, expires_at=expires_at)
