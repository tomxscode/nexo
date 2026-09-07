from django.contrib import admin

from .models import Quotation, QuotationEvent, QuotationItem


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0


class QuotationEventInline(admin.TabularInline):
    model = QuotationEvent
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("folio", "client", "status", "payment_terms", "total", "valid_until")
    list_filter = ("tenant", "status")
    search_fields = ("folio", "client__name")
    inlines = [QuotationItemInline, QuotationEventInline]


class QuotationEventInline(admin.TabularInline):
    model = QuotationEvent
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(QuotationEvent)
class QuotationEventAdmin(admin.ModelAdmin):
    list_display = ("quotation", "action", "by_name", "by_email", "created_at")
    list_filter = ("action",)
    search_fields = ("quotation__folio", "by_name", "by_email")