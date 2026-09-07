from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.decorators import tenant_required

from .forms import CategoryForm, ProductForm
from .models import Category, Product


@tenant_required
def index(request):
    tenant = request.user.current_tenant
    q = request.GET.get("q", "").strip()
    kind = request.GET.get("kind", "")
    category_pk = request.GET.get("category", "")

    products = tenant.products.filter(active=True)
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(code__icontains=q) | Q(category__name__icontains=q)
        )
    if kind in ("producto", "servicio"):
        products = products.filter(kind=kind)
    if category_pk.isdigit():
        products = products.filter(category_id=category_pk)

    products = products.select_related("category")

    total_items = products.count()
    margen_promedio = 0
    valor_inventario = Decimal("0")
    priced = [p for p in products if p.price_net > 0]
    if priced:
        margen_promedio = sum(p.margin_percent for p in priced) / len(priced)
    if kind in ("producto", "servicio"):
        pass
    valor_inventario = sum(p.inventory_value for p in products if p.kind == Product.Kind.PRODUCT)

    categories = tenant.categories.all()
    category_form = CategoryForm(request.POST or None)
    if request.method == "POST" and "category" in request.POST and category_form.is_valid():
        category_form.instance.tenant = tenant
        category_form.save()
        messages.success(request, "Categoría agregada.")
        return redirect("products:index")

    return render(
        request,
        "products/index.html",
        {
            "products": products,
            "categories": categories,
            "q": q,
            "kind": kind,
            "category_pk": category_pk,
            "total_items": total_items,
            "margen_promedio": margen_promedio,
            "valor_inventario": valor_inventario,
            "category_form": category_form,
        },
    )


@tenant_required
def create(request):
    tenant = request.user.current_tenant
    form = ProductForm(request.POST or None, tenant=tenant)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.tenant = tenant
        if not product.code:
            product.code = f"ID-{tenant.products.count() + 1:04d}"
        product.save()
        messages.success(request, f"{product.name} agregado al catálogo.")
        return redirect("products:index")
    return render(request, "products/form.html", {"form": form, "is_edit": False})


@tenant_required
def update(request, pk):
    tenant = request.user.current_tenant
    product = get_object_or_404(Product, pk=pk, tenant=tenant)
    form = ProductForm(request.POST or None, instance=product, tenant=tenant)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{product.name} actualizado.")
        return redirect("products:index")
    return render(request, "products/form.html", {"form": form, "product": product, "is_edit": True})