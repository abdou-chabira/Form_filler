import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CheckTemplateUploadForm
from .models import CheckTemplate


def template_list(request):
    templates = CheckTemplate.objects.order_by("-created_at")
    return render(request, "paycheck/template_list.html", {"templates": templates})


def template_create(request):
    if request.method == "POST":
        form = CheckTemplateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            messages.success(request, "Template uploaded. Now mark each text area.")
            return redirect("paycheck:template_design", template_id=template.id)
    else:
        form = CheckTemplateUploadForm()

    return render(request, "paycheck/template_create.html", {"form": form})


def template_design(request, template_id):
    template = get_object_or_404(CheckTemplate, id=template_id)

    def safe_float(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    if request.method == "POST":
        raw_fields = request.POST.get("fields_json", "[]")
        try:
            parsed_fields = json.loads(raw_fields)
        except json.JSONDecodeError:
            messages.error(request, "Invalid field data. Please try saving again.")
            return redirect("paycheck:template_design", template_id=template.id)

        valid_fields = []
        used_keys = set()
        for item in parsed_fields:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip().replace(" ", "_")
            label = str(item.get("label", key)).strip() or key
            if not key:
                continue
            base_key = key
            suffix = 2
            while key in used_keys:
                key = f"{base_key}_{suffix}"
                suffix += 1
            used_keys.add(key)
            valid_fields.append(
                {
                    "key": key,
                    "label": label,
                    "x": max(0, min(100, safe_float(item.get("x", 0), 0))),
                    "y": max(0, min(100, safe_float(item.get("y", 0), 0))),
                    "w": max(0.1, min(100, safe_float(item.get("w", 10), 10))),
                    "h": max(0.1, min(100, safe_float(item.get("h", 5), 5))),
                    "font_size_mm": max(1.5, min(12, safe_float(item.get("font_size_mm", 3.5), 3.5))),
                }
            )

        if not valid_fields:
            messages.error(request, "No fields were saved. Draw at least one field area before saving.")
            return redirect("paycheck:template_design", template_id=template.id)

        template.fields = valid_fields
        template.save(update_fields=["fields"])
        messages.success(request, "Template fields saved.")
        return redirect("paycheck:template_fill", template_id=template.id)

    return render(
        request,
        "paycheck/template_design.html",
        {
            "template": template,
            "existing_fields_json": json.dumps(template.fields),
        },
    )


def template_fill(request, template_id):
    template = get_object_or_404(CheckTemplate, id=template_id)

    if request.method == "POST":
        values = {}
        for field in template.fields:
            key = field.get("key")
            if not key:
                continue
            values[key] = request.POST.get(key, "")

        request.session[f"template_values_{template.id}"] = values
        return redirect("paycheck:template_print", template_id=template.id)

    return render(request, "paycheck/template_fill.html", {"template": template})


def template_print(request, template_id):
    template = get_object_or_404(CheckTemplate, id=template_id)
    values = request.session.get(f"template_values_{template.id}", {})

    return render(
        request,
        "paycheck/template_print.html",
        {
            "template": template,
            "values": values,
        },
    )
