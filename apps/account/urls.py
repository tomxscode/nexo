from django.urls import path
from django.urls import reverse_lazy

from .views import LogoutView, NexoLoginView, onboarding, profile, set_theme, signup

app_name = "account"

urlpatterns = [
    path("login/", NexoLoginView.as_view(), name="login"),
    path(
        "logout/",
        LogoutView.as_view(next_page=reverse_lazy("account:login")),
        name="logout",
    ),
    path("signup/", signup, name="signup"),
    path("onboarding/", onboarding, name="onboarding"),
    path("perfil/", profile, name="profile"),
    path("tema/", set_theme, name="theme"),
]