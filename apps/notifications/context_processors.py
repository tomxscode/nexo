from .models import Notification, sweep_expiring


def bell(request):
    """Contexto de la campana: sweep de vencimientos + datos del usuario actual."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    tenant = user.current_tenant
    if tenant is None:
        return {}
    sweep_expiring(tenant)
    recent = Notification.objects.filter(user=user)[:8]
    unread = Notification.objects.filter(user=user, is_read=False).count()
    return {"notifications_recent": recent, "unread_count": unread}