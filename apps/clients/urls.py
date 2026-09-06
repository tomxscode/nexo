from django.urls import path

from .views import index

app_name = "clients"

urlpatterns = [
    path("", index, name="index"),
]
