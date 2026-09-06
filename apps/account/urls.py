from django.urls import path

from .views import LogoutView, NexoLoginView, onboarding, signup

app_name = "account"

urlpatterns = [
    path("login/", NexoLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", signup, name="signup"),
    path("onboarding/", onboarding, name="onboarding"),
]