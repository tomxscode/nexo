from django.urls import path

from .views import bell, mark_all_read, mark_read

app_name = "notifications"

urlpatterns = [
    path("_bell/", bell, name="bell"),
    path("leer/<int:pk>/", mark_read, name="mark_read"),
    path("leer/todas/", mark_all_read, name="mark_all_read"),
]