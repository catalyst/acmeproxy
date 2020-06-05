from django.contrib import admin

from .models import *

class AuthorisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'created_by_ip')
    fields = ('name', 'secret')

class ResponseAdmin(admin.ModelAdmin):
    list_display = ('name', 'response', 'created_at', 'expired_at', 'live', 'created_by_ip')

admin.site.register(Authorisation, AuthorisationAdmin)
admin.site.register(Response, ResponseAdmin)
