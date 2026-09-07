from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import tenant_required

from .models import DeliveryTemplate, Order, OrderStage


@tenant_required
def index(request):
    tenant = request.user.current_tenant
    payment = request.GET.get("payment", "todas")

    orders = (
        tenant.orders.select_related("client")
        .prefetch_related("items", "stages")
        .order_by("-created_at")
    )
    if payment in (c[0] for c in Order.Payment.choices):
        orders = orders.filter(payment_status=payment)

    total_pendiente = Decimal("0")
    total_pagado = Decimal("0")
    for order in orders:
        if order.payment_status == Order.Payment.PAID:
            total_pagado += order.total
        else:
            total_pendiente += order.total

    return render(
        request,
        "orders/index.html",
        {
            "orders": orders,
            "payment": payment,
            "total_pendiente": total_pendiente,
            "total_pagado": total_pagado,
        },
    )


@tenant_required
def detail(request, pk):
    tenant = request.user.current_tenant
    order = get_object_or_404(
        Order.objects.select_related("client", "quotation").prefetch_related(
            "items__product", "stages"
        ),
        pk=pk,
        tenant=tenant,
    )

    if request.method == "POST":
        action = request.POST.get("action")

        blocked_while_delivered = {
            "apply_template",
            "add_stage",
            "stage_advance",
            "stage_reopen",
            "stage_delete",
        }
        if order.delivered and action in blocked_while_delivered:
            messages.error(
                request,
                f"{order.folio} ya fue entregado: no se pueden modificar ni agregar etapas.",
            )
            return redirect("orders:detail", pk=order.pk)

        if action == "pay_full":
            order.register_payment(percent=100)
            messages.success(request, f"{order.folio} registrado como totalmente pagado.")
            return redirect("orders:detail", pk=order.pk)

        if action == "pay_percent":
            raw = request.POST.get("percent", "").strip()
            try:
                percent = int(round(float(raw)))
            except (TypeError, ValueError):
                percent = 0
            percent = max(0, min(100, percent))
            order.register_payment(percent=percent)
            if percent <= 0:
                messages.info(request, f"{order.folio} sin abonos registrados.")
            elif percent >= 100:
                messages.success(request, f"{order.folio} registrado como totalmente pagado.")
            else:
                messages.success(request, f"{order.folio} con abono de {percent}% registrado.")
            return redirect("orders:detail", pk=order.pk)

        if action == "apply_template":
            tpl = (
                DeliveryTemplate.objects.filter(pk=request.POST.get("template_pk"), tenant=tenant).first()
                if request.POST.get("template_pk")
                else None
            )
            if tpl:
                existing = set(order.stages.values_list("name", flat=True))
                added = 0
                for raw_name in tpl.stages:
                    name = (raw_name or "").strip()[:140]
                    if name and name not in existing:
                        OrderStage.objects.create(order=order, name=name)
                        existing.add(name)
                        added += 1
                order.recalc_delivery()
                messages.success(request, f"Plantilla “{tpl.name}” aplicada ({added} etapas agregadas).")
            return redirect("orders:detail", pk=order.pk)

        if action == "add_stage":
            name = request.POST.get("name", "").strip()
            planned = request.POST.get("planned_date", "").strip()
            if name:
                OrderStage.objects.create(
                    order=order,
                    name=name[:140],
                    planned_date=planned or None,
                )
                order.recalc_delivery()
                messages.success(request, "Etapa agregada al pedido.")
            return redirect("orders:detail", pk=order.pk)

        stage_pk = request.POST.get("stage_pk")
        stage = (
            OrderStage.objects.filter(pk=stage_pk, order=order).first()
            if stage_pk
            else None
        )
        if action == "stage_advance" and stage:
            stage.advance()
            messages.success(request, f"Etapa avanzada: {stage.name}.")
        elif action == "stage_reopen" and stage:
            stage.reopen()
            messages.success(request, f"Etapa reabierta: {stage.name}.")
        elif action == "stage_delete" and stage:
            stage.delete()
            order.recalc_delivery()
            messages.success(request, f"Etapa eliminada: {stage.name}.")
        return redirect("orders:detail", pk=order.pk)

    return render(
        request,
        "orders/detail.html",
        {"order": order, "templates": tenant.delivery_templates.all()},
    )


@tenant_required
@require_POST
def pay(request, pk):
    tenant = request.user.current_tenant
    order = get_object_or_404(Order, pk=pk, tenant=tenant)
    if order.payment_status != Order.Payment.PAID:
        order.register_payment(percent=100)
        messages.success(request, f"{order.folio} registrado como pagado.")
    return redirect("orders:detail", pk=order.pk)


@tenant_required
def templates(request):
    tenant = request.user.current_tenant

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            lines = [
                line.strip()
                for line in request.POST.get("stages", "").splitlines()
                if line.strip()
            ]
            if name and lines:
                DeliveryTemplate.objects.create(
                    tenant=tenant,
                    name=name[:140],
                    stages=[line[:140] for line in lines],
                    is_system=False,
                )
                messages.success(request, f"Plantilla “{name}” creada.")
            elif not name:
                messages.error(request, "Escribe un nombre para la plantilla.")
            else:
                messages.error(request, "Agrega al menos una etapa en el listado.")
        elif action == "delete":
            tpl = DeliveryTemplate.objects.filter(
                pk=request.POST.get("template_pk"), tenant=tenant
            ).first()
            if tpl:
                tpl.delete()
                messages.success(request, f"Plantilla “{tpl.name}” eliminada.")
        return redirect("orders:templates")

    return render(
        request,
        "orders/templates.html",
        {"templates": tenant.delivery_templates.all()},
    )