from django import forms

from .models import Category, Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "code",
            "name",
            "category",
            "kind",
            "unit",
            "price_net",
            "cost",
            "iva_rate",
            "stock",
            "active",
        )
        widgets = {
            "code": forms.TextInput(attrs={"class": "input", "placeholder": "P-001"}),
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Nombre del ítem"}
            ),
            "category": forms.Select(attrs={"class": "input"}),
            "kind": forms.Select(attrs={"class": "input"}),
            "unit": forms.TextInput(attrs={"class": "input", "placeholder": "unidad"}),
            "price_net": forms.NumberInput(
                attrs={"class": "input text-tabular", "step": "0.01", "min": "0"}
            ),
            "cost": forms.NumberInput(
                attrs={"class": "input text-tabular", "step": "0.01", "min": "0"}
            ),
            "iva_rate": forms.NumberInput(
                attrs={"class": "input text-tabular", "step": "0.01", "min": "0"}
            ),
            "stock": forms.NumberInput(
                attrs={"class": "input text-tabular", "step": "0.001", "min": "0"}
            ),
            "active": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-outline-variant text-primary-container focus:ring-primary-container"
                }
            ),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["category"].queryset = Category.objects.filter(tenant=tenant)


class CategoryForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "input", "placeholder": "Nueva categoría"}
        ),
        label="",
    )

    class Meta:
        model = Category
        fields = ("name",)