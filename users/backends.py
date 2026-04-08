from django.contrib.auth.backends import BaseBackend
from .models import TallyUser


class PhoneOTPBackend(BaseBackend):
    """Authenticate via phone number — actual OTP check is done in the view."""

    def authenticate(self, request, phone_number=None, **kwargs):
        if not phone_number:
            return None
        try:
            return TallyUser.objects.get(phone_number=phone_number, is_active=True)
        except TallyUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return TallyUser.objects.get(pk=user_id)
        except TallyUser.DoesNotExist:
            return None
