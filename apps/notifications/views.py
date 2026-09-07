from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.core.decorators import tenant_required

from .models import Notification


def _bell(request):
    """Fragmento de la campana (usable en GET e htmx)."""
    scope = request.user.notifications
    recent = scope.all()[:8]
    unread = scope.filter(is_read=False).count()
    return render(
        request,
        "notifications/_bell.html",
        {"notifications_recent": recent, "unread_count": unread},
    )


@tenant_required
def bell(request):
    return _bell(request)


@tenant_required
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    unread = request.user.notifications.filter(is_read=False).count()
    return render(
        request,
        "notifications/_read_redirect.html",
        {"unread_count": unread, "url": notification.link},
    )


@tenant_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return _bell(request)