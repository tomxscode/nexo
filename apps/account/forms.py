from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify

from apps.core.models import Tenant, User


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "tu@correo.cl", "autocomplete": "email"}),
        label="Correo electrónico",
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Tu nombre"}),
        label="Nombre",
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Tu apellido"}),
        label="Apellido",
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "••••••••", "autocomplete": "new-password"}),
        label="Contraseña",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "Repite tu contraseña", "autocomplete": "new-password"}),
        label="Confirmar contraseña",
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.is_active = True
        if commit:
            user.save()
        return user


class OnboardingForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Ej: Ferretería Los Álamos"}),
        label="Nombre del negocio",
    )
    rut = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Ej: 12.345.678-9"}),
        label="RUT",
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "input", "placeholder": "contacto@negocio.cl"}),
        label="Email de contacto",
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "+56 9 1234 5678"}),
        label="Teléfono",
    )
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Dirección comercial"}),
        label="Dirección",
    )
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={"class": "input py-2.5", "accept": "image/*"}),
        label="Logo (opcional)",
    )
    default_iva = forms.DecimalField(
        widget=forms.NumberInput(attrs={"class": "input", "step": "0.01", "value": 19}),
        label="IVA por defecto (%)",
    )

    class Meta:
        model = Tenant
        fields = ("name", "rut", "email", "phone", "address", "logo", "default_iva")

    def save(self, commit=True):
        tenant = super().save(commit=False)
        base = slugify(tenant.name) or "negocio"
        slug = base
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            counter += 1
            slug = f"{base}-{counter}"
        tenant.slug = slug
        if commit:
            tenant.save()
        return tenant