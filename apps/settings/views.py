import secrets

from django.contrib import messages
from django.shortcuts import redirect, render

from apps.core.decorators import tenant_required
from apps.core.models import TenantMembership, User

from .forms import MemberAddForm, TenantForm


def _is_manager(user, tenant):
    return TenantMembership.objects.filter(
        tenant=tenant, user=user, role__in=[TenantMembership.Role.OWNER, TenantMembership.Role.ADMIN]
    ).exists()


@tenant_required
def index(request):
    tenant = request.user.current_tenant
    can_manage = _is_manager(request.user, tenant)

    if can_manage and request.method == "POST":
        action = request.POST.get("action")
        if action == "save_business":
            form = TenantForm(request.POST, request.FILES, instance=tenant)
            if form.is_valid():
                form.save()
                messages.success(request, "Datos del negocio actualizados.")
                return redirect("settings:index")
        elif action == "add_member":
            add_form = MemberAddForm(request.POST)
            if add_form.is_valid():
                email = add_form.cleaned_data["email"].lower()
                role = add_form.cleaned_data["role"]
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={"username": email, "is_active": True},
                )
                if created:
                    temp = secrets.token_urlsafe(6)
                    user.set_password(temp)
                    user.save(update_fields=["password"])
                    messages.success(
                        request,
                        f"Miembro creado. Contraseña temporal: {temp} (guárdala, no se vuelve a mostrar).",
                    )
                else:
                    messages.info(request, "Usuario existente vinculado al negocio.")
                TenantMembership.objects.get_or_create(
                    user=user,
                    tenant=tenant,
                    defaults={
                        "role": role,
                        "is_owner": role == TenantMembership.Role.OWNER,
                    },
                )
                return redirect("settings:index")
        elif action == "role":
            mid = request.POST.get("member_pk")
            new_role = request.POST.get("role")
            if mid and new_role:
                TenantMembership.objects.filter(pk=mid, tenant=tenant).update(role=new_role)
                messages.success(request, "Rol actualizado.")
            return redirect("settings:index")
        elif action == "remove":
            mid = request.POST.get("member_pk")
            if mid:
                my_pk = TenantMembership.objects.filter(tenant=tenant, user=request.user).values_list("pk", flat=True).first()
                if int(mid) == my_pk:
                    messages.error(request, "No puedes eliminarte a ti mismo.")
                else:
                    TenantMembership.objects.filter(pk=mid, tenant=tenant).delete()
                    messages.success(request, "Miembro eliminado.")
            return redirect("settings:index")

    form = TenantForm(instance=tenant)
    add_form = MemberAddForm()
    members = list(
        TenantMembership.objects.filter(tenant=tenant)
        .select_related("user")
        .order_by("-is_owner", "role", "user__email")
    )
    return render(
        request,
        "settings/index.html",
        {
            "form": form,
            "add_form": add_form,
            "members": members,
            "roles": TenantMembership.Role.choices,
            "can_manage": can_manage,
            "my_pk": TenantMembership.objects.filter(tenant=tenant, user=request.user).values_list("pk", flat=True).first(),
        },
    )