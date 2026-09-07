from django import forms

from apps.core.models import Tenant, TenantMembership


class TenantForm(forms.ModelForm):
    currency = forms.ChoiceField(
        choices=[("CLP", "CLP"), ("USD", "USD"), ("UF", "UF")],
        widget=forms.Select(attrs={"class": "input"}),
        label="Moneda",
    )

    class Meta:
        model = Tenant
        fields = (
            "name",
            "rut",
            "email",
            "phone",
            "address",
            "giro",
            "delivery_terms",
            "warranty",
            "logo",
            "default_iva",
            "currency",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Nombre del negocio"}
            ),
            "rut": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ej: 12.345.678-9"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "input", "placeholder": "contacto@negocio.cl"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "input", "placeholder": "+56 9 1234 5678"}
            ),
            "address": forms.TextInput(
                attrs={"class": "input", "placeholder": "Dirección"}
            ),
            "giro": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ej: Comercio minorista"}
            ),
            "delivery_terms": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ej: 3 días corridos"}
            ),
            "warranty": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ej: 6 meses"}
            ),
            "logo": forms.ClearableFileInput(
                attrs={"class": "input py-2.5", "accept": "image/*"}
            ),
            "default_iva": forms.NumberInput(
                attrs={"class": "input", "step": "0.01"}
            ),
        }


class MemberAddForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "input", "placeholder": "correo@ejemplo.cl"}
        ),
        label="Correo",
    )
    role = forms.ChoiceField(
        choices=[
            (v, l) for v, l in TenantMembership.Role.choices if v != TenantMembership.Role.OWNER
        ],
        initial=TenantMembership.Role.SALES,
        widget=forms.Select(attrs={"class": "input"}),
        label="Rol",
    )