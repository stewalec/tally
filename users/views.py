from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

import plivo
from django.conf import settings

from .forms import LoginForm, OTPForm, ProfileForm
from .models import OTPCode, TallyUser


def _send_otp_sms(phone_number: str, code: str):
    client = plivo.RestClient(settings.PLIVO_AUTH_ID, settings.PLIVO_AUTH_TOKEN)
    client.messages.create(
        src=settings.PLIVO_PHONE_NUMBER,
        dst=phone_number,
        text=f"Your Tally login code is: {code}\n\nThis code expires in {settings.OTP_EXPIRY_MINUTES} minutes.",
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone_number"]
            try:
                user = TallyUser.objects.get(phone_number=phone, is_active=True)
            except TallyUser.DoesNotExist:
                messages.error(request, "That phone number is not registered with Tally.")
                return render(request, "auth/login.html", {"form": form})

            otp = OTPCode.generate_for(user)
            try:
                _send_otp_sms(phone, otp.code)
            except Exception:
                messages.error(request, "Failed to send SMS. Please try again.")
                return render(request, "auth/login.html", {"form": form})

            request.session["otp_phone"] = phone
            return redirect("verify")
    else:
        form = LoginForm()

    return render(request, "auth/login.html", {"form": form})


def verify_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    phone = request.session.get("otp_phone")
    if not phone:
        return redirect("login")

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            try:
                user = TallyUser.objects.get(phone_number=phone, is_active=True)
                otp = OTPCode.objects.filter(user=user, code=code, used=False).order_by("-created_at").first()
                if otp and otp.is_valid:
                    otp.used = True
                    otp.save()
                    auth.login(request, user, backend="users.backends.PhoneOTPBackend")
                    request.session.pop("otp_phone", None)
                    return redirect("/")
                else:
                    messages.error(request, "Invalid or expired code. Please try again.")
            except TallyUser.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect("login")
    else:
        form = OTPForm()

    masked = "•••" + phone[-4:] if len(phone) >= 4 else phone
    return render(request, "auth/verify.html", {"form": form, "masked_phone": masked})


def logout_view(request):
    if request.method == "POST":
        auth.logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            new_username = form.cleaned_data["username"]
            if TallyUser.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                form.add_error("username", "That username is already taken.")
            else:
                user.first_name = form.cleaned_data["first_name"]
                user.last_name = form.cleaned_data["last_name"]
                user.username = new_username
                user.save(update_fields=["first_name", "last_name", "username"])
                messages.success(request, "Profile updated.")
                return redirect("profile")
    else:
        form = ProfileForm(initial={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
        })

    return render(request, "users/profile.html", {"form": form})
