from django.urls import path

from .views import create, index, update

app_name = "clients"

urlpatterns = [
    path("", index, name="index"),
    path("nuevo/", create, name="create"),
    path("<int:pk>/editar/", update, name="update"),
]