from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    return render(
        request,
        "workspace/module_placeholder.html",
        {
            "module_title": "Pedidos",
            "module_description": "Este módulo se construye en la siguiente fase.",
        },
    )
