from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ("name", "rut", "giro", "email", "phone", "address", "notes", "active")
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Cliente o empresa"}
            ),
            "rut": forms.TextInput(
                attrs={"class": "input", "placeholder": "12.345.678-9"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "input", "placeholder": "cliente@correo.cl"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "input", "placeholder": "+56 9 1234 5678"}
            ),
            "address": forms.TextInput(
                attrs={"class": "input", "placeholder": "Dirección"}
            ),
            "giro": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ej: Comercio minorista / Venta por internet"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "input min-h-[96px] py-2.5", "rows": 4}
            ),
            "active": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-outline-variant text-primary-container focus:ring-primary-container"
                }
            ),
        }