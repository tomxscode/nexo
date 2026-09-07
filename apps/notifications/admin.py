from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("text", "user", "category", "is_read", "created_at")
    list_filter = ("category", "is_read", "tenant")
    search_fields = ("text", "user__email", "quotation__folio")
    raw_id_fields = ("user", "quotation")