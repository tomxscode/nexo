from django.db import migrations

SISTEMA = "Envío a domicilio"
ETAPAS = ["Procesando envío", "Entregado a transportista", "Entregado"]


def seed_templates(apps, schema_editor):
    Tenant = apps.get_model("core", "Tenant")
    DeliveryTemplate = apps.get_model("orders", "DeliveryTemplate")
    for tenant in Tenant.objects.all():
        DeliveryTemplate.objects.get_or_create(
            tenant=tenant,
            name=SISTEMA,
            defaults={"stages": ETAPAS, "is_system": True},
        )


def remove_seeded(apps, schema_editor):
    DeliveryTemplate = apps.get_model("orders", "DeliveryTemplate")
    DeliveryTemplate.objects.filter(name=SISTEMA, is_system=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_f2_plantillas_pagos'),
    ]

    operations = [
        migrations.RunPython(seed_templates, remove_seeded),
    ]