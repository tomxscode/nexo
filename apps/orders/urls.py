from django.urls import path

from .views import detail, index, pay, templates

app_name = "orders"

urlpatterns = [
    path("", index, name="index"),
    path("<int:pk>/", detail, name="detail"),
    path("<int:pk>/pagar/", pay, name="pay"),
    path("plantillas/", templates, name="templates"),
]