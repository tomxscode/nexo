from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.orders.models import Order


PERIODS = {
    "este_mes": "Este mes",
    "mes_pasado": "Mes pasado",
    "ult_30d": "Últimos 30 días",
    "ult_3m": "Últimos 3 meses",
    "anio": "Este año",
    "todo": "Todo",
}


def _month_start(d):
    return d.replace(day=1)


def _bounds(period, today):
    """Devuelve (start, end, prev_start, prev_end, prev_label) o None* cuando aplica.

    Los rangos son [inicio, fin) con datetimes."""
    today_dt = timezone.make_aware(
        timezone.datetime(today.year, today.month, today.day)
    )

    def span(day_start, day_end_exclusive):
        return (
            timezone.make_aware(timezone.datetime(day_start.year, day_start.month, day_start.day)),
            timezone.make_aware(timezone.datetime(day_end_exclusive.year, day_end_exclusive.month, day_end_exclusive.day)),
        )

    if period == "este_mes":
        start = _month_start(today)
        end = _month_start(today + timedelta(days=32))
        prev_start = _month_start(start - timedelta(days=1))
        prev_end = start
    elif period == "mes_pasado":
        prev_prev = _month_start(today - timedelta(days=32))
        start = _month_start(today - timedelta(days=32))
        end = _month_start(today)
        prev_start = _month_start(prev_prev - timedelta(days=1))
        prev_end = start
    elif period == "ult_30d":
        start = today - timedelta(days=29)
        end = today + timedelta(days=1)
        prev_start = start - timedelta(days=30)
        prev_end = start
    elif period == "ult_3m":
        start = today - timedelta(days=89)
        end = today + timedelta(days=1)
        prev_start = start - timedelta(days=90)
        prev_end = start
    elif period == "anio":
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31) + timedelta(days=1)
        prev_start = start.replace(year=start.year - 1)
        prev_end = start
    else:  # todo
        return (None, None, None, None, None)

    return span(start, end) + span(prev_start, prev_end) + (PERIODS[period],)


def _sum_total(qs):
    return qs.aggregate(s=Sum("total"))["s"] or Decimal("0")


def _delta(cur, prev):
    if prev in (None, 0):
        return None
    return (cur - prev) / prev * 100


def _compute(request, tenant):
    period = request.GET.get("periodo", "este_mes")
    if period not in PERIODS:
        period = "este_mes"
    today = timezone.localdate()
    start, end, prev_start, prev_end, prev_label = _bounds(period, today)

    def in_range(qs, s, e):
        if s is None:
            return qs
        return qs.filter(created_at__gte=s, created_at__lt=e)

    quotations = tenant.quotations.all()
    orders = tenant.orders.all()

    active_codes = ("enviada", "vista", "aprobada")
    venta = _sum_total(in_range(orders, start, end))
    venta_prev = _sum_total(in_range(orders, prev_start, prev_end))

    paid_now = orders.filter(
        payment_status=Order.Payment.PAID, paid_at__gte=start, paid_at__lt=end
    ) if start is not None else orders.filter(payment_status=Order.Payment.PAID)
    cobros = _sum_total(paid_now)
    cobros_prev = _sum_total(
        orders.filter(
            payment_status=Order.Payment.PAID, paid_at__gte=prev_start, paid_at__lt=prev_end
        )
    ) if prev_start is not None else Decimal("0")
    pagadas_now = paid_now.count()
    pagadas_prev = (
        orders.filter(
            payment_status=Order.Payment.PAID, paid_at__gte=prev_start, paid_at__lt=prev_end
        ).count()
        if prev_start is not None
        else 0
    )

    pendiente_cobro = _sum_total(orders.exclude(payment_status=Order.Payment.PAID))

    qs_now = in_range(quotations, start, end)
    qs_prev = in_range(quotations, prev_start, prev_end)
    cartera = _sum_total(qs_now.filter(status__in=active_codes))
    cartera_prev = _sum_total(qs_prev.filter(status__in=active_codes))
    enviadas = qs_now.filter(status__in=("enviada", "vista")).count()
    enviadas_prev = qs_prev.filter(status__in=("enviada", "vista")).count()
    aprobadas = qs_now.filter(status="aprobada").count()
    aprobadas_prev = qs_prev.filter(status="aprobada").count()
    match = aprobadas + enviadas
    match_prev = aprobadas_prev + enviadas_prev
    conversion = aprobadas / match * 100 if match else 0
    conversion_prev = aprobadas_prev / match_prev * 100 if match_prev else 0

    quotation_value = _sum_total(
        qs_now.filter(status__in=("enviada", "vista", "aprobada", "convertida"))
    )
    ticket_promedio = cobros / pagadas_now if pagadas_now else Decimal("0")

    kpis = [
        {
            "label": "Ventas del periodo",
            "value": venta,
            "money": True,
            "icon": "trending_up",
            "delta": _delta(venta, venta_prev),
            "delta_label": f"vs {prev_label}",
            "sub": f"{len(in_range(orders, start, end))} pedidos",
        },
        {
            "label": "Cartera abierta",
            "value": cartera,
            "money": True,
            "icon": "request_quote",
            "delta": _delta(cartera, cartera_prev),
            "delta_label": f"vs {prev_label}",
            "sub": f"{enviadas} cotizaciones en curso",
        },
        {
            "label": "Tasa de conversión",
            "value": f"{conversion:.0f}%",
            "money": False,
            "icon": "verified",
            "delta": _delta(conversion, conversion_prev),
            "delta_label": f"vs {prev_label}",
            "sub": f"{aprobadas} aprobadas · {enviadas} en curso",
        },
        {
            "label": "Ticket promedio",
            "value": ticket_promedio,
            "money": True,
            "icon": "payments",
            "delta": None,
            "delta_label": None,
            "sub": f"{pagadas_now} ventas pagadas",
        },
    ]

    # ---- Alertas / pendientes ----
    por_vencer = []
    for q in quotations.filter(
        status__in=("enviada", "vista"), valid_until__gte=today
    ).order_by("valid_until")[:5]:
        por_vencer.append({"q": q, "days_left": (q.valid_until - today).days})
    por_cobrar_count = orders.exclude(payment_status=Order.Payment.PAID).count()
    en_entrega_count = orders.filter(delivered_at__isnull=True).count()

    # ---- Estados (periodo elegido) ----
    estados_cotizacion = []
    for code, label in [
        ("borrador", "Borrador"),
        ("enviada", "Enviadas"),
        ("vista", "Vistas"),
        ("aprobada", "Aprobadas"),
        ("rechazada", "Rechazadas"),
        ("convertida", "Convertidas"),
    ]:
        estados_cotizacion.append((label, qs_now.filter(status=code).count(), code))
    total_estados = sum(n for _, n, _ in estados_cotizacion) or 1
    estados_cotizacion = [
        (label, n, code, n / total_estados * 100) for label, n, code in estados_cotizacion
    ]

    return {
        "tenant": tenant,
        "today": today,
        "period": period,
        "periods": PERIODS,
        "period_label": PERIODS[period],
        "prev_label": prev_label or "",
        "kpis": kpis,
        "venta_periodo": venta,
        "cobros_periodo": cobros,
        "pendiente_cobro": pendiente_cobro,
        "quotation_value": quotation_value,
        "cartera": cartera,
        "conversion": conversion,
        "enviadas": enviadas,
        "aprobadas": aprobadas,
        "por_vencer": por_vencer,
        "por_cobrar_count": por_cobrar_count,
        "en_entrega_count": en_entrega_count,
        "estados_cotizacion": estados_cotizacion,
        "total_cotizaciones": qs_now.count(),
        "recientes": list(quotations.select_related("client")[:5]),
        "ultimos_pedidos": list(orders.select_related("client")[:5]),
        "pedidos": orders.count(),
        "year": today.year,
        "month": today.month,
        "buscas_prev": prev_start is not None,
    }


@login_required
def index(request):
    tenant = request.user.current_tenant
    if tenant is None:
        return render(request, "dashboard/index.html", {"tenant_missing": True})

    cargo = _compute(request, tenant)
    if getattr(request, "htmx", None):
        return render(request, "dashboard/_content.html", cargo)
    return render(request, "dashboard/index.html", cargo)