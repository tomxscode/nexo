from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("folio", "name", "rut", "giro", "phone", "active")
    list_filter = ("tenant", "active")
    search_fields = ("name", "rut")