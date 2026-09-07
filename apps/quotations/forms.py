from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from apps.products.models import Product

from .models import Quotation, QuotationItem

PAYMENT_TERMS_OPTIONS = [
    "Pago inmediato / transferencia",
    "Contra entrega",
    "50% anticipo y 50% contra entrega",
    "Crédito a 30 días",
    "Crédito a 60 días",
    "Crédito a 90 días",
]
PAYMENT_TERMS_CUSTOM = "__custom__"


class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = (
            "product",
            "description",
            "quantity",
            "unit_price_net",
            "discount_percent",
            "iva_rate",
        )
        widgets = {
            "product": forms.Select(attrs={"class": "input input-sm", "data-field": "product"}),
            "description": forms.TextInput(
                attrs={"class": "input input-sm", "data-field": "description", "placeholder": "Descripción"}
            ),
            "quantity": forms.NumberInput(
                attrs={"class": "input input-sm text-tabular", "data-field": "quantity", "step": "0.01", "min": "0", "value": "1"}
            ),
            "unit_price_net": forms.NumberInput(
                attrs={"class": "input input-sm text-tabular", "data-field": "price", "step": "0.01", "min": "0"}
            ),
            "discount_percent": forms.NumberInput(
                attrs={"class": "input input-sm text-tabular", "data-field": "discount", "step": "0.01", "min": "0", "max": "100", "value": "0"}
            ),
            "iva_rate": forms.NumberInput(
                attrs={"class": "input input-sm text-tabular", "data-field": "iva", "step": "0.01", "min": "0", "value": "19"}
            ),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["product"].queryset = Product.objects.filter(tenant=tenant, active=True).order_by("name")
        self.fields["product"].empty_label = "— Producto / servicio —"


QuotationItemFormSet = inlineformset_factory(
    Quotation, QuotationItem, form=QuotationItemForm, extra=2, can_delete=True
)


class QuotationForm(forms.ModelForm):
    payment_terms = forms.ChoiceField(
        choices=[(term, term) for term in PAYMENT_TERMS_OPTIONS]
        + [(PAYMENT_TERMS_CUSTOM, "— Otra (escríbela) —")],
        widget=forms.Select(attrs={"class": "input"}),
        label="Forma de pago",
        required=False,
    )
    payment_terms_custom = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "input", "placeholder": "Ej: 40% al aprobar y 60% a la entrega"}
        ),
        required=False,
        label="Otra forma de pago",
    )

    class Meta:
        model = Quotation
        fields = ("client", "issue_date", "valid_until", "payment_terms", "discount", "notes")
        widgets = {
            "client": forms.Select(attrs={"class": "input"}),
            "issue_date": forms.DateInput(
                attrs={"class": "input", "type": "date"}, format="%Y-%m-%d"
            ),
            "valid_until": forms.DateInput(
                attrs={"class": "input", "type": "date"}, format="%Y-%m-%d"
            ),
            "discount": forms.NumberInput(
                attrs={"class": "input text-tabular", "step": "0.01", "min": "0", "placeholder": "0"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "input min-h-[80px] py-2.5", "rows": 3, "placeholder": "Condiciones, plazos, garantías…"}
            ),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["client"].queryset = tenant.clients.filter(active=True).order_by("name")
        self.fields["client"].empty_label = "— Selecciona cliente —"

        # En edición, si la forma guardada no está entre las opciones -> personalizada
        instance_value = self.instance.payment_terms if self.instance and self.instance.pk else ""
        if instance_value and instance_value not in PAYMENT_TERMS_OPTIONS:
            if not self.is_bound:
                self.fields["payment_terms"].initial = PAYMENT_TERMS_CUSTOM
                self.fields["payment_terms_custom"].initial = instance_value
            elif self.data.get("payment_terms") == PAYMENT_TERMS_CUSTOM:
                self.fields["payment_terms_custom"].initial = instance_value

    def clean(self):
        cleaned = super().clean()
        terms = cleaned.get("payment_terms")
        custom = (cleaned.get("payment_terms_custom") or "").strip()
        if terms == PAYMENT_TERMS_CUSTOM:
            if not custom:
                self.add_error("payment_terms_custom", "Escribe la forma de pago personalizada.")
            else:
                cleaned["payment_terms"] = custom
        elif not terms:
            cleaned["payment_terms"] = "Pago inmediato / transferencia"
        return cleaned