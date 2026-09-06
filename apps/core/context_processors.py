from django.urls import reverse

NAV = [
    {"label": "Dashboard", "icon": "dashboard", "namespace": "dashboard"},
    {"label": "Cotizaciones", "icon": "request_quote", "namespace": "quotations"},
    {"label": "Clientes", "icon": "group", "namespace": "clients"},
    {"label": "Pedidos", "icon": "inventory_2", "namespace": "orders"},
    {"label": "Productos", "icon": "shopping_bag", "namespace": "products"},
    {"label": "Configuración", "icon": "settings", "namespace": "settings"},
]


def workspace(request):
    """Contexto global: tenant activo, sección de navegación actual, y items del nav."""

    user = getattr(request, "user", None)
    current_tenant = None
    if user is not None and user.is_authenticated:
        current_tenant = user.current_tenant

    namespaces = request.resolver_match.namespaces if request.resolver_match else []
    nav_section = namespaces[-1] if namespaces else ""

    nav_items = []
    for item in NAV:
        try:
            url = reverse(f"{item['namespace']}:index")
        except Exception:
            url = "#"
        nav_items.append(
            {
                "label": item["label"],
                "icon": item["icon"],
                "url": url,
                "active": item["namespace"] == nav_section,
            }
        )

    return {
        "current_tenant": current_tenant,
        "nav_section": nav_section,
        "nav_items": nav_items,
    }