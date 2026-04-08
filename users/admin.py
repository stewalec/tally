from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import TallyUser, OTPCode


@admin.register(TallyUser)
class TallyUserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "username", "first_name", "last_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff")
    search_fields = ("phone_number", "username", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")
    fieldsets = (
        (None, {"fields": ("phone_number", "username", "is_active")}),
        ("Name", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("date_joined", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "first_name", "last_name", "username", "is_active", "is_staff"),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            # Adding a new user — no password needed
            form.base_fields.pop("password", None)
        return form

    def save_model(self, request, obj, form, change):
        if not change:
            # Normalize phone on creation
            from users.models import normalize_phone
            obj.phone_number = normalize_phone(obj.phone_number) or obj.phone_number
            obj.set_unusable_password()
        obj.save()


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "expires_at", "used")
    list_filter = ("used",)
    search_fields = ("user__phone_number",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
