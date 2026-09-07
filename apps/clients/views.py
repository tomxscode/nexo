from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.decorators import tenant_required

from .forms import ClientForm
from .models import Client


@tenant_required
def index(request):
    tenant = request.user.current_tenant
    q = request.GET.get("q", "").strip()

    clients = tenant.clients.filter(active=True)
    if q:
        clients = clients.filter(
            Q(name__icontains=q)
            | Q(rut__icontains=q)
            | Q(email__icontains=q)
            | Q(phone__icontains=q)
        )

    sel_pk = request.GET.get("sel")
    selected = clients.filter(pk=sel_pk).first() if sel_pk else None
    if selected is None:
        selected = clients.first()

    return render(
        request,
        "clients/index.html",
        {"clients": clients, "selected": selected, "q": q},
    )


@tenant_required
def create(request):
    tenant = request.user.current_tenant
    form = ClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        client = form.save(commit=False)
        client.tenant = tenant
        client.folio = tenant.next_client_folio()
        client.save()
        messages.success(request, f"Cliente {client.name} creado.")
        return redirect("clients:index")
    return render(request, "clients/form.html", {"form": form, "is_edit": False})


@tenant_required
def update(request, pk):
    tenant = request.user.current_tenant
    client = get_object_or_404(Client, pk=pk, tenant=tenant)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{client.name} actualizado.")
        return redirect("clients:index")
    return render(request, "clients/form.html", {"form": form, "client": client, "is_edit": True})