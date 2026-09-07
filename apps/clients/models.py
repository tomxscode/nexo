from django.db import models

from apps.core.models import Tenant


class Client(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="clients"
    )
    folio = models.CharField("Folio", max_length=20, editable=False)
    name = models.CharField("Nombre / Razón social", max_length=160)
    rut = models.CharField("RUT", max_length=20, blank=True, default="")
    giro = models.CharField("Giro", max_length=120, blank=True, default="")
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Teléfono", max_length=32, blank=True, default="")
    address = models.CharField("Dirección", max_length=200, blank=True, default="")
    notes = models.TextField("Notas", blank=True)
    active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "folio"], name="unique_tenant_client_folio"
            )
        ]

    def __str__(self):
        return self.name