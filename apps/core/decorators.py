from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def tenant_required(view):
    """Exige sesión y negocio activo; sin tenant redirige al onboarding."""

    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.current_tenant is None:
            return redirect("account:onboarding")
        return view(request, *args, **kwargs)

    return _wrapped