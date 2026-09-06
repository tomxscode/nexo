from django.urls import path

from .views import index

app_name = "quotations"

urlpatterns = [
    path("", index, name="index"),
]
