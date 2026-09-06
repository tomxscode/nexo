from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class Tenant(models.Model):
    """Un negocio registrado en Nexo (workspace aislado por tenant_id)."""

    class Plan(models.TextChoices):
        FREE = "free", "Gratis"
        GROW = "grow", "Crecimiento"
        PRO = "pro", "Pro"

    name = models.CharField("Nombre del negocio", max_length=120)
    slug = models.SlugField("Slug", max_length=120, unique=True)

    rut = models.CharField("RUT", max_length=20, blank=True, default="")
    email = models.EmailField("Email de contacto", blank=True)
    phone = models.CharField("Teléfono", max_length=32, blank=True, default="")
    address = models.CharField("Dirección", max_length=200, blank=True, default="")

    logo = models.ImageField("Logo", upload_to="logos/", blank=True)

    currency = models.CharField("Moneda", max_length=8, default="CLP")
    default_iva = models.DecimalField(
        "IVA por defecto (%)",
        max_digits=5,
        decimal_places=2,
        default=19.00,
        validators=[MinValueValidator(0)],
    )

    # Folios correlativos
    next_client_number = models.PositiveIntegerField(default=1)
    next_quotation_number = models.PositiveIntegerField(default=1)
    next_order_number = models.PositiveIntegerField(default=1)

    plan = models.CharField(
        "Plan", max_length=16, choices=Plan.choices, default=Plan.FREE
    )
    active = models.BooleanField("Activo", default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Negocio (tenant)"
        verbose_name_plural = "Negocios (tenants)"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def client_prefix(self):
        return "CLI-"

    @property
    def quotation_prefix(self):
        return "COT-"

    @property
    def order_prefix(self):
        return "PED-"

    def next_client_folio(self):
        folio = f"{self.client_prefix}{self.next_client_number:04d}"
        self.next_client_number += 1
        self.save(update_fields=["next_client_number"])
        return folio

    def next_quotation_folio(self):
        folio = f"{self.quotation_prefix}{self.next_quotation_number:04d}"
        self.next_quotation_number += 1
        self.save(update_fields=["next_quotation_number"])
        return folio

    def next_order_folio(self):
        folio = f"{self.order_prefix}{self.next_order_number:04d}"
        self.next_order_number += 1
        self.save(update_fields=["next_order_number"])
        return folio


class User(AbstractUser):
    """Usuario de Nexo. Se autentica con email."""

    email = models.EmailField("Correo electrónico", unique=True)
    current_tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_users",
        verbose_name="Negocio activo",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email


class TenantMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Propietario"
        ADMIN = "admin", "Administrador"
        SALES = "sales", "Ventas"
        VIEWER = "viewer", "Solo lectura"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        "Rol", max_length=16, choices=Role.choices, default=Role.SALES
    )
    is_owner = models.BooleanField("Propietario", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Miembro"
        verbose_name_plural = "Miembros"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant"], name="unique_user_tenant"
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.tenant} ({self.role})"