from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from apps.core.models import TenantMembership

from .forms import OnboardingForm, SignupForm


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
        messages.success(
            request,
            f"¡{tenant.name} ya está operando en Nexo! Cuentas gratis por ahora.",
        )
        return redirect("dashboard:index")

    return render(request, "account/onboarding.html", {"form": form})