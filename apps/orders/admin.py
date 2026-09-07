from django.contrib import admin

from .models import DeliveryTemplate, Order, OrderItem, OrderStage


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderStageInline(admin.TabularInline):
    model = OrderStage
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("folio", "client", "payment_status", "delivered_at", "total", "created_at")
    list_filter = ("tenant", "payment_status")
    search_fields = ("folio", "client__name")
    inlines = [OrderItemInline, OrderStageInline]


@admin.register(OrderStage)
class OrderStageAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "status", "planned_date", "completed_at")
    list_filter = ("status",)


@admin.register(DeliveryTemplate)
class DeliveryTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "is_system", "created_at")
    list_filter = ("tenant", "is_system")
    search_fields = ("name", "tenant__name")