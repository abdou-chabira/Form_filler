from django import forms

from .models import CheckTemplate


class CheckTemplateUploadForm(forms.ModelForm):
    class Meta:
        model = CheckTemplate
        fields = ["name", "image", "width_mm", "height_mm"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Payroll check template"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "width_mm": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "10"}),
            "height_mm": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "10"}),
        }
