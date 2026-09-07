from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.core.models import Tenant, TenantMembership, User
from apps.orders.models import DeliveryTemplate

from .forms import NexoPasswordChangeForm, OnboardingForm, ProfileForm, SignupForm


class NexoLoginView(LoginView):
    template_name = "account/login.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class or AuthenticationForm)
        form.fields["username"].widget.attrs.update(
            {"class": "input", "placeholder": "tu@correo.cl", "autocomplete": "email"}
        )
        form.fields["username"].label = "Correo electrónico"
        form.fields["password"].widget.attrs.update(
            {"class": "input", "placeholder": "••••••••", "autocomplete": "current-password"}
        )
        return form


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "¡Bienvenido a Nexo! Crea tu negocio para comenzar.")
        return redirect("account:onboarding")

    return render(request, "account/signup.html", {"form": form})


@login_required
def onboarding(request):
    if request.user.current_tenant is not None:
        return redirect("dashboard:index")

    form = OnboardingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        tenant = form.save()
        TenantMembership.objects.create(
            user=request.user, tenant=tenant, role=TenantMembership.Role.OWNER, is_owner=True
        )
        request.user.current_tenant = tenant
        request.user.save(update_fields=["current_tenant"])
        DeliveryTemplate.objects.create(
            tenant=tenant,
            name="Envío a domicilio",
            stages=["Procesando envío", "Entregado a transportista", "Entregado"],
            is_system=True,
        )
        messages.success(
            request,
            f"¡{tenant.name} ya está operando en Nexo! Cuentas gratis por ahora.",
        )
        return redirect("dashboard:index")

    return render(request, "account/onboarding.html", {"form": form})


@login_required
def profile(request):
    profile_form = ProfileForm(request.POST or None, instance=request.user)
    password_form = NexoPasswordChangeForm(request.user, request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Perfil actualizado.")
                return redirect("account:profile")
        elif action == "password":
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Contraseña actualizada.")
                return redirect("account:profile")
        elif action == "switch_tenant":
            tenant_pk = request.POST.get("tenant")
            memberships = request.user.memberships.all()
            target = memberships.filter(pk=tenant_pk).first() if tenant_pk else None
            if target:
                request.user.current_tenant = target.tenant
                request.user.save(update_fields=["current_tenant"])
                messages.success(request, f"Negocio activo: {target.tenant.name}")
                return redirect("dashboard:index")

    return render(
        request,
        "account/profile.html",
        {
            "profile_form": profile_form,
            "password_form": password_form,
            "memberships": request.user.memberships.select_related("tenant").order_by("-is_owner"),
        },
    )


@login_required
@require_POST
def set_theme(request):
    theme = request.POST.get("theme")
    if theme in dict(User.Theme.choices):
        request.user.theme = theme
        request.user.save(update_fields=["theme"])
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "error": "theme inválido"}, status=400)