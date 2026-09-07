from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.money import dec as _dec
from apps.core.models import Tenant, User


class Order(models.Model):
    class Payment(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        PARTIAL = "parcial", "Abonado parcial"
        PAID = "pagado", "Pagado"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="orders"
    )
    folio = models.CharField("Folio", max_length=20, editable=False)
    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="orders"
    )
    quotation = models.OneToOneField(
        "quotations.Quotation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
        verbose_name="Cotización origen",
    )
    payment_status = models.CharField(
        "Estado de cobro",
        max_length=16,
        choices=Payment.choices,
        default=Payment.PENDING,
    )
    progress = models.PositiveSmallIntegerField("Avance (%)", default=0)
    delivered_at = models.DateTimeField("Entregado el", null=True, blank=True)
    paid_at = models.DateTimeField("Pagado el", null=True, blank=True)

    subtotal_net = models.DecimalField(
        "Subtotal neto", max_digits=16, decimal_places=2, default=0
    )
    iva_amount = models.DecimalField(
        "IVA", max_digits=16, decimal_places=2, default=0
    )
    total = models.DecimalField("Total", max_digits=16, decimal_places=2, default=0)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "folio"], name="unique_tenant_order_folio"
            )
        ]

    def __str__(self):
        return self.folio

    @property
    def paid_amount(self):
        return _dec(Decimal(self.total) * self.progress / 100)

    @property
    def unpaid_amount(self):
        return _dec(Decimal(self.total) - Decimal(self.paid_amount))

    def register_payment(self, percent=100):
        """Registra un abono como % del total. 0 = pendiente, 100 = pagado."""
        percent = max(0, min(100, int(percent)))
        if percent <= 0:
            self.payment_status = self.Payment.PENDING
            self.progress = 0
            self.paid_at = None
        elif percent >= 100:
            self.payment_status = self.Payment.PAID
            self.progress = 100
            self.paid_at = timezone.now()
        else:
            self.payment_status = self.Payment.PARTIAL
            self.progress = percent
            self.paid_at = None
        self.save(update_fields=["payment_status", "progress", "paid_at", "updated_at"])

    @property
    def delivered(self):
        return self.delivered_at is not None

    @property
    def delivery_progress(self):
        stages = list(self.stages.all())
        if not stages:
            return None
        done = sum(1 for s in stages if s.status == OrderStage.Status.DONE)
        return round(done * 100 / len(stages))

    def recalc_delivery(self):
        """Auto-completa la entrega al llegar a 100% y la reabre si baja."""
        progress = self.delivery_progress
        if progress is None:
            return
        if progress >= 100 and not self.delivered:
            self.delivered_at = timezone.now()
            self.save(update_fields=["delivered_at", "updated_at"])
        elif progress < 100 and self.delivered:
            self.delivered_at = None
            self.save(update_fields=["delivered_at", "updated_at"])

    def register_delivery(self):
        if not self.delivered_at:
            self.delivered_at = timezone.now()
            self.save(update_fields=["delivered_at", "updated_at"])


class DeliveryTemplate(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="delivery_templates",
        verbose_name="Negocio",
    )
    name = models.CharField("Nombre de la plantilla", max_length=140)
    stages = models.JSONField("Etapas", default=list, blank=True)
    is_system = models.BooleanField("Sugerida por Nexo", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plantilla de etapas"
        verbose_name_plural = "Plantillas de etapas"
        ordering = ["-is_system", "name", "id"]

    def __str__(self):
        return self.name


class OrderStage(models.Model):
    class Status(models.TextChoices):
        PENDING = "pendiente", "Pendiente"
        PROCESS = "en_proceso", "En proceso"
        DONE = "completada", "Completada"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="stages", verbose_name="Pedido"
    )
    name = models.CharField("Hito / etapa", max_length=140)
    planned_date = models.DateField("Fecha estimada", null=True, blank=True)
    status = models.CharField(
        "Estado", max_length=16, choices=Status.choices, default=Status.PENDING
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas de entrega"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} ({self.order.folio})"

    def advance(self):
        if self.status == self.Status.PENDING:
            self.status = self.Status.PROCESS
        elif self.status == self.Status.PROCESS:
            self.status = self.Status.DONE
            self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "order_id"])
        self.order.recalc_delivery()

    def reopen(self):
        self.status = self.Status.PENDING
        self.completed_at = None
        self.save(update_fields=["status", "completed_at"])
        self.order.recalc_delivery()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    description = models.CharField("Descripción", max_length=200)
    quantity = models.DecimalField(
        "Cantidad", max_digits=12, decimal_places=2, default=1
    )
    unit_price_net = models.DecimalField(
        "Precio unitario neto", max_digits=14, decimal_places=2, default=0
    )
    iva_rate = models.DecimalField(
        "IVA (%)", max_digits=5, decimal_places=2, default=19
    )

    def line_total(self):
        return _dec(self.quantity * self.unit_price_net)