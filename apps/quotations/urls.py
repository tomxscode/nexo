from django.urls import path

from .views import convert, create, delete, detail, edit, index, pdf, public, send

app_name = "quotations"

urlpatterns = [
    path("", index, name="index"),
    path("nueva/", create, name="create"),
    path("<int:pk>/", detail, name="detail"),
    path("<int:pk>/editar/", edit, name="edit"),
    path("<int:pk>/enviar/", send, name="send"),
    path("<int:pk>/convertir/", convert, name="convert"),
    path("<int:pk>/eliminar/", delete, name="delete"),
    path("c/<uuid:token>/", public, name="public"),
    path("c/<uuid:token>/pdf/", pdf, name="pdf"),
]