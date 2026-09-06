from django.urls import path

from .views import index

app_name = "settings"

urlpatterns = [
    path("", index, name="index"),
]
