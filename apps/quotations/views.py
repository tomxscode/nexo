import uuid
from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from apps.core.decorators import tenant_required
from apps.notifications.models import Notification, notify_team
from apps.orders.models import Order, OrderItem
from apps.products.models import Product

from .forms import QuotationForm, QuotationItemFormSet
from .models import Quotation, QuotationEvent


def _product_data(tenant):
    return [
        {
            "id": str(p.pk),
            "name": p.name,
            "description": p.name,
            "price": str(p.price_net),
            "iva": str(p.iva_rate),
        }
        for p in Product.objects.filter(tenant=tenant, active=True)
    ]


def _status_counts(tenant):
    qs = tenant.quotations.all()
    counts = {"todas": qs.count()}
    for status, _ in Quotation.Status.choices:
        counts[status] = qs.filter(status=status).count()
    return counts


def _clean_vencer(raw):
    try:
        days = int(raw)
        return days if 1 <= days <= 365 else None
    except (TypeError, ValueError):
        return None


@tenant_required
def index(request):
    tenant = request.user.current_tenant
    status = request.GET.get("status", "todas")
    vencer = _clean_vencer(request.GET.get("vencer"))
    qs = tenant.quotations.select_related("client")
    if status in (s[0] for s in Quotation.Status.choices):
        qs = qs.filter(status=status)
    if vencer is not None:
        from django.utils import timezone

        qs = qs.filter(
            status__in=[Quotation.Status.SENT, Quotation.Status.VIEWED],
            valid_until__lte=timezone.localdate() + timedelta(days=vencer),
        )

    return render(
        request,
        "quotations/index.html",
        {"quotations": qs, "status": status, "vencer": vencer, "counts": _status_counts(tenant)},
    )


@tenant_required
def create(request):
    tenant = request.user.current_tenant
    initial = {}
    client_param = request.GET.get("client")
    if client_param and client_param.isdigit():
        initial["client"] = int(client_param)
    form = QuotationForm(request.POST or None, tenant=tenant, initial=initial)
    formset = QuotationItemFormSet(request.POST or None, form_kwargs={"tenant": tenant})

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                quotation = form.save(commit=False)
                quotation.tenant = tenant
                quotation.folio = tenant.next_quotation_folio()
                quotation.created_by = request.user
                quotation.save()
                formset.instance = quotation
                formset.save()
                quotation.recalc()
            messages.success(request, f"Cotización {quotation.folio} creada.")
            quotation.log_event(QuotationEvent.Action.CREATED)
            return redirect("quotations:detail", pk=quotation.pk)

    return render(
        request,
        "quotations/form.html",
        {"form": form, "formset": formset, "is_edit": False, "products_json": _product_data(tenant)},
    )


@tenant_required
def edit(request, pk):
    tenant = request.user.current_tenant
    quotation = get_object_or_404(Quotation, pk=pk, tenant=tenant)
    form = QuotationForm(request.POST or None, instance=quotation, tenant=tenant)
    formset = QuotationItemFormSet(request.POST or None, instance=quotation, form_kwargs={"tenant": tenant})

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
            quotation.recalc()
        messages.success(request, f"{quotation.folio} actualizada.")
        return redirect("quotations:detail", pk=quotation.pk)

    return render(
        request,
        "quotations/form.html",
        {"form": form, "formset": formset, "quotation": quotation, "is_edit": True, "products_json": _product_data(tenant)},
    )


@tenant_required
def detail(request, pk):
    tenant = request.user.current_tenant
    quotation = get_object_or_404(
        Quotation.objects.select_related("client").prefetch_related(
            "items__product", "events"
        ),
        pk=pk,
        tenant=tenant,
    )
    public_url = reverse_public(request, quotation)
    return render(
        request,
        "quotations/detail.html",
        {"quotation": quotation, "public_url": public_url},
    )


def reverse_public(request, quotation):
    from django.urls import reverse

    return request.build_absolute_uri(
        reverse("quotations:public", kwargs={"token": quotation.approval_token})
    )


@tenant_required
@require_POST
def send(request, pk):
    tenant = request.user.current_tenant
    quotation = get_object_or_404(Quotation, pk=pk, tenant=tenant)
    if quotation.status in (Quotation.Status.DRAFT, Quotation.Status.REJECTED):
        quotation.status = Quotation.Status.SENT
        quotation.save(update_fields=["status", "updated_at"])
        quotation.log_event(QuotationEvent.Action.SENT)
        messages.success(
            request,
            f"{quotation.folio} enviada. Comparte el link público con tu cliente.",
        )
    return redirect("quotations:detail", pk=quotation.pk)


@tenant_required
@require_POST
def convert(request, pk):
    tenant = request.user.current_tenant
    quotation = get_object_or_404(
        Quotation.objects.prefetch_related("items"), pk=pk, tenant=tenant
    )
    if quotation.status != Quotation.Status.APPROVED:
        messages.error(request, "Solo puedes convertir cotizaciones aprobadas.")
        return redirect("quotations:detail", pk=quotation.pk)

    with transaction.atomic():
        order = Order.objects.create(
            tenant=tenant,
            folio=tenant.next_order_folio(),
            client=quotation.client,
            quotation=quotation,
            subtotal_net=quotation.subtotal_net,
            iva_amount=quotation.iva_amount,
            total=quotation.total,
            created_by=request.user,
        )
        for item in quotation.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                description=item.description,
                quantity=item.quantity,
                unit_price_net=item.unit_price_net,
                iva_rate=item.iva_rate,
            )
        quotation.status = Quotation.Status.CONVERTED
        quotation.save(update_fields=["status", "updated_at"])
        quotation.log_event(QuotationEvent.Action.CONVERTED)

    messages.success(request, f"{quotation.folio} convertida en {order.folio}.")
    return redirect("orders:index")


@tenant_required
@require_POST
def delete(request, pk):
    tenant = request.user.current_tenant
    quotation = get_object_or_404(Quotation, pk=pk, tenant=tenant)
    if quotation.status not in (Quotation.Status.DRAFT, Quotation.Status.REJECTED):
        messages.error(request, "Solo se eliminan borradores o cotizaciones rechazadas.")
    else:
        quotation.delete()
        messages.success(request, "Cotización eliminada.")
    return redirect("quotations:index")


def public(request, token):
    """Link público de aprobación sin autenticación."""
    quotation = get_object_or_404(
        Quotation.objects.select_related("client", "tenant").prefetch_related("items__product"),
        approval_token=token,
    )

    if request.method == "POST" and quotation.is_approvable:
        action = request.POST.get("action")
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        comment = request.POST.get("comment", "").strip()
        if action == "aprobar":
            if not name:
                messages.error(request, "Ingresa tu nombre para aprobar la cotización.")
            elif not email:
                messages.error(request, "Ingresa tu correo para aprobar la cotización.")
            else:
                approved = quotation.approve(name=name, email=email, comment=comment)
                if approved:
                    notify_team(
                        quotation.tenant,
                        Notification.Category.APPROVED,
                        f"{quotation.folio} fue aprobada por {name} "
                        f"({email}). Valor {quotation.total}.",
                        quotation=quotation,
                        link=reverse("quotations:detail", args=[quotation.pk]),
                    )
                    messages.success(request, "¡Cotización aprobada! Gracias por confirmar.")
        elif action == "rechazar":
            rejected = quotation.reject(comment=comment)
            if rejected:
                notify_team(
                    quotation.tenant,
                    Notification.Category.REJECTED,
                    f"{quotation.folio} fue rechazada"
                    + (f": “{comment}”" if comment else "."),
                    quotation=quotation,
                    link=reverse("quotations:detail", args=[quotation.pk]),
                )
                messages.info(request, "Cotización rechazada. El negocio lo notará.")
        return redirect("quotations:public", token=token)

    # Primera visita de una cotización enviada -> marca como vista
    if quotation.status == Quotation.Status.SENT:
        quotation.status = Quotation.Status.VIEWED
        quotation.save(update_fields=["status", "updated_at"])
        quotation.log_event(QuotationEvent.Action.VIEWED)
        notify_team(
            quotation.tenant,
            Notification.Category.VIEWED,
            f"{quotation.folio} fue vista por tu cliente {quotation.client.name}.",
            quotation=quotation,
            link=reverse("quotations:detail", args=[quotation.pk]),
        )

    return render(request, "quotations/public.html", {"quotation": quotation})


def pdf(request, token):
    quotation = get_object_or_404(
        Quotation.objects.select_related("client", "tenant").prefetch_related("items__product"),
        approval_token=token,
    )
    html = render_to_string("pdf/quotation.html", {"quotation": quotation})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{quotation.folio}.pdf"'
    pisa.CreatePDF(html, dest=response, encoding="utf-8")
    return response