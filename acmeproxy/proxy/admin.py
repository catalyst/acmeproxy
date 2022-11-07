from django.contrib import admin

from .models import Authorisation, Account, Response
from .utils import client_ip

# XXX: save_model() is identical on all ModelAdmin instances, how to do this properly


class AuthorisationAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "created_at", "created_by_ip")
    fields = ("name", "account", "secret")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by_ip = client_ip(request)

        super().save_model(request, obj, form, change)


class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "created_by_ip")
    fields = ("name", "secret", "permit_domains", "notes")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by_ip = client_ip(request)

        super().save_model(request, obj, form, change)


class ResponseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "response",
        "created_at",
        "expired_at",
        "live",
        "created_by_ip",
    )
    fields = ("name", "response")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by_ip = client_ip(request)

        super().save_model(request, obj, form, change)


admin.site.register(Authorisation, AuthorisationAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Response, ResponseAdmin)
