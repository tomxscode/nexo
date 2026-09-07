import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.money import dec as _dec
from apps.core.models import Tenant, User


def _default_valid_until():
    return timezone.localdate() + timedelta(days=30)


class Quotation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "borrador", "Borrador"
        SENT = "enviada", "Enviada"
        VIEWED = "vista", "Vista"
        APPROVED = "aprobada", "Aprobada"
        REJECTED = "rechazada", "Rechazada"
        CONVERTED = "convertida", "Convertida"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="quotations"
    )
    folio = models.CharField("Folio", max_length=20, editable=False)
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="quotations",
        verbose_name="Cliente",
    )
    status = models.CharField(
        "Estado", max_length=16, choices=Status.choices, default=Status.DRAFT
    )
    issue_date = models.DateField("Fecha de emisión", default=timezone.localdate)
    valid_until = models.DateField(
        "Válida hasta",
        default=_default_valid_until,
    )
    notes = models.TextField("Condiciones / notas", blank=True)
    payment_terms = models.CharField(
        "Forma de pago", max_length=140, blank=True, default="Pago inmediato / transferencia"
    )
    discount = models.DecimalField(
        "Descuento", max_digits=14, decimal_places=2, default=0
    )

    subtotal_net = models.DecimalField(
        "Subtotal neto", max_digits=16, decimal_places=2, default=0
    )
    iva_amount = models.DecimalField(
        "IVA", max_digits=16, decimal_places=2, default=0
    )
    total = models.DecimalField("Total", max_digits=16, decimal_places=2, default=0)

    approval_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by_name = models.CharField(max_length=120, blank=True, default="")
    approved_by_email = models.EmailField("Correo del aprobador", blank=True, default="")
    approval_comment = models.TextField("Comentario del cliente", blank=True, default="")

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="quotations",
        verbose_name="Creada por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "folio"], name="unique_tenant_quotation_folio"
            )
        ]

    def __str__(self):
        return f"{self.folio} · {self.client.name}"

    def recalc(self, save=True):
        subtotal = Decimal("0")
        for item in self.items.all():
            subtotal += item.line_total()
        iva = sum((item.line_total() * item.iva_rate / 100 for item in self.items.all()), Decimal("0"))
        self.subtotal_net = _dec(subtotal)
        self.iva_amount = _dec(iva)
        self.total = _dec(subtotal + iva - self.discount)
        if save:
            self.save(
                update_fields=["subtotal_net", "iva_amount", "total", "updated_at"]
            )

    def approve(self, name="", email="", comment=""):
        if self.status not in (self.Status.SENT, self.Status.VIEWED):
            return False
        self.status = self.Status.APPROVED
        self.approved_at = timezone.now()
        self.approved_by_name = name or self.client.name
        self.approved_by_email = email
        self.approval_comment = comment
        self.save(
            update_fields=[
                "status",
                "approved_at",
                "approved_by_name",
                "approved_by_email",
                "approval_comment",
            ]
        )
        self.log_event(
            QuotationEvent.Action.APPROVED,
            name=self.approved_by_name,
            email=email,
            comment=comment,
        )
        return True

    def reject(self, comment=""):
        if self.status not in (self.Status.SENT, self.Status.VIEWED):
            return False
        self.status = self.Status.REJECTED
        if comment:
            self.approval_comment = comment
        self.save(update_fields=["status", "approval_comment"])
        self.log_event(QuotationEvent.Action.REJECTED, comment=comment)
        return True

    def log_event(self, action, name="", email="", comment=""):
        return QuotationEvent.objects.create(
            quotation=self, action=action, by_name=name, by_email=email, comment=comment
        )

    @property
    def net_total(self):
        """Neto después del descuento global (sin IVA)."""
        return _dec(self.subtotal_net - self.discount)

    @property
    def is_approvable(self):
        return self.status in (self.Status.SENT, self.Status.VIEWED)


class QuotationEvent(models.Model):
    class Action(models.TextChoices):
        CREATED = "creada", "Creada"
        SENT = "enviada", "Enviada"
        VIEWED = "vista", "Vista"
        APPROVED = "aprobada", "Aprobada"
        REJECTED = "rechazada", "Rechazada"
        CONVERTED = "convertida", "Convertida"

    quotation = models.ForeignKey(
        Quotation, on_delete=models.CASCADE, related_name="events", verbose_name="Cotización"
    )
    action = models.CharField("Acción", max_length=16, choices=Action.choices)
    by_name = models.CharField(max_length=120, blank=True, default="")
    by_email = models.EmailField(max_length=254, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField("Fecha", auto_now_add=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Historial"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} · {self.created_at:%d/%m/%Y %H:%M}"


class QuotationItem(models.Model):
    quotation = models.ForeignKey(
        Quotation, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quotation_items",
    )
    description = models.CharField("Descripción", max_length=200)
    quantity = models.DecimalField(
        "Cantidad", max_digits=12, decimal_places=2, default=1
    )
    unit_price_net = models.DecimalField(
        "Precio unitario neto", max_digits=14, decimal_places=2, default=0
    )
    discount_percent = models.DecimalField(
        "Dto. %", max_digits=6, decimal_places=2, default=0
    )
    iva_rate = models.DecimalField(
        "IVA (%)", max_digits=5, decimal_places=2, default=19
    )

    def line_total(self):
        return _dec(
            self.quantity
            * self.unit_price_net
            * (1 - self.discount_percent / 100)
        )

    def line_iva(self):
        return _dec(self.line_total() * self.iva_rate / 100)

    def line_gross(self):
        return _dec(self.line_total() + self.line_iva())