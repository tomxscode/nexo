from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind", "price_net", "stock", "active")
    list_filter = ("tenant", "kind", "category", "active")
    search_fields = ("name", "code")