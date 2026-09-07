from django.db import models
from django.utils import timezone

from apps.core.models import Tenant, User


class Notification(models.Model):
    class Category(models.TextChoices):
        VIEWED = "vista", "Cotización vista"
        APPROVED = "aprobada", "Cotización aprobada"
        REJECTED = "rechazada", "Cotización rechazada"
        EXPIRING = "por_vencer", "Cotización por vencer"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="notifications"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Destinatario",
    )
    category = models.CharField(
        "Categoría", max_length=16, choices=Category.choices
    )
    text = models.CharField("Texto", max_length=255)
    link = models.CharField("Destino", max_length=255, blank=True, default="")
    quotation = models.ForeignKey(
        "quotations.Quotation",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
        verbose_name="Cotización",
    )
    threshold = models.PositiveSmallIntegerField(
        "Umbral (días)", null=True, blank=True
    )
    is_read = models.BooleanField("Leída", default=False)
    created_at = models.DateTimeField("Fecha", auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user", "category", "quotation", "threshold"],
                name="unique_tenant_user_category_quote_threshold",
            )
        ]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.text}"


def team_users(tenant):
    """Miembros del negocio con rol de trabajo (owner/admin/sales)."""
    from apps.core.models import TenantMembership

    return User.objects.filter(
        memberships__tenant=tenant,
        memberships__role__in=[
            TenantMembership.Role.OWNER,
            TenantMembership.Role.ADMIN,
            TenantMembership.Role.SALES,
        ],
    )


def notify_team(
    tenant, category, text, quotation=None, threshold=None, link="", skip_user=None
):
    created = 0
    for user in team_users(tenant).exclude(pk=skip_user.pk if skip_user else None):
        defaults = {"text": text, "link": link}
        if threshold is not None:
            defaults["threshold"] = threshold
        _, was_created = Notification.objects.get_or_create(
            tenant=tenant,
            user=user,
            category=category,
            quotation=quotation,
            threshold=threshold,
            defaults=defaults,
        )
        created += int(was_created)
    return created


EXPIRING_BUCKETS = (15, 10, 5, 1)


def sweep_expiring(tenant=None):
    """Genera notificaciones por vencimiento (idempotente).

    Umbrales 15, 10, 5 y 1 día para cotizaciones enviadas o vistas. Si recibe un
    tenant solo recorre ese negocio (sweep a petición); si es None recorre todos.
    """
    from django.urls import reverse

    from apps.quotations.models import Quotation

    qs = Quotation.objects.filter(
        status__in=[Quotation.Status.SENT, Quotation.Status.VIEWED],
        valid_until__gte=timezone.localdate(),
    )
    if tenant is not None:
        qs = qs.filter(tenant=tenant)

    created = 0
    for quotation in qs.select_related("tenant"):
        days_left = (quotation.valid_until - timezone.localdate()).days
        link = reverse("quotations:detail", args=[quotation.pk])
        for bucket in EXPIRING_BUCKETS:
            if days_left > bucket:
                continue
            if days_left > 1:
                text = (
                    f"{quotation.folio} vence en {days_left} días "
                    f"({quotation.client.name})."
                )
            else:
                text = (
                    f"{quotation.folio} vence HOY ({quotation.client.name}). "
                    "¡Segui a tu cliente!"
                )
            created += notify_team(
                quotation.tenant,
                Notification.Category.EXPIRING,
                text,
                quotation=quotation,
                threshold=bucket,
                link=link,
            )
    return created
