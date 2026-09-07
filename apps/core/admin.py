from django.contrib import admin

from apps.core.models import Tenant, TenantMembership, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "rut", "plan", "active", "created_at")
    list_filter = ("plan", "active")
    search_fields = ("name", "slug", "rut")
    fieldsets = (
        (None, {"fields": ("name", "slug", "rut", "email", "phone", "address", "logo")}),
        ("Datos comerciales", {"fields": ("giro", "delivery_terms", "warranty", "currency", "default_iva")}),
        ("Folios", {"fields": ("next_client_number", "next_quotation_number", "next_order_number")}),
        ("Plan", {"fields": ("plan", "active")}),
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "current_tenant", "is_active")
    search_fields = ("email", "first_name", "last_name")


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role", "is_owner")