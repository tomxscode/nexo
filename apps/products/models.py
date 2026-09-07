from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import Tenant


class Category(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField("Nombre", max_length=80)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"], name="unique_tenant_category_name"
            )
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    class Kind(models.TextChoices):
        PRODUCT = "producto", "Producto"
        SERVICE = "servicio", "Servicio"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="products"
    )
    code = models.CharField("Código", max_length=40, blank=True, default="")
    name = models.CharField("Nombre", max_length=160)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Categoría",
    )
    kind = models.CharField(
        "Tipo", max_length=16, choices=Kind.choices, default=Kind.PRODUCT
    )
    unit = models.CharField("Unidad", max_length=24, default="unidad")
    price_net = models.DecimalField(
        "Precio neto", max_digits=14, decimal_places=2, default=0
    )
    cost = models.DecimalField(
        "Costo", max_digits=14, decimal_places=2, default=0
    )
    iva_rate = models.DecimalField(
        "IVA (%)",
        max_digits=5,
        decimal_places=2,
        default=19,
        validators=[MinValueValidator(0)],
    )
    stock = models.DecimalField(
        "Stock", max_digits=12, decimal_places=3, default=0
    )
    active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto / Servicio"
        verbose_name_plural = "Productos / Servicios"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "code"], name="unique_tenant_product_code"
            )
        ]

    def __str__(self):
        return self.name

    @property
    def price_gross(self):
        return self.price_net * (1 + self.iva_rate / 100)

    @property
    def margin_percent(self):
        if self.price_net <= 0:
            return 0
        return (self.price_net - self.cost) / self.price_net * 100

    @property
    def inventory_value(self):
        return self.stock * self.cost