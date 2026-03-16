import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CheckTemplateUploadForm
from .models import CheckTemplate


def number_to_french(n):
    units = [
        "zero",
        "un",
        "deux",
        "trois",
        "quatre",
        "cinq",
        "six",
        "sept",
        "huit",
        "neuf",
        "dix",
        "onze",
        "douze",
        "treize",
        "quatorze",
        "quinze",
        "seize",
    ]
    tens = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante"]

    if n < 0:
        return "moins " + number_to_french(-n)

    if n < 17:
        return units[n]

    if n < 20:
        return "dix-" + units[n - 10]

    if n < 70:
        t = n // 10
        u = n % 10
        word = tens[t]
        if u == 1:
            return word + "-et-un"
        if u > 0:
            return word + "-" + units[u]
        return word

    if n < 80:
        if n == 71:
            return "soixante-et-onze"
        return "soixante-" + number_to_french(n - 60)

    if n < 100:
        if n == 80:
            return "quatre-vingts"
        return "quatre-vingt-" + number_to_french(n - 80)

    if n < 1000:
        h = n // 100
        r = n % 100
        if h == 1:
            prefix = "cent"
        else:
            prefix = units[h] + " cent"

        if r == 0:
            return prefix
        return prefix + " " + number_to_french(r)

    if n < 1_000_000:
        th = n // 1000
        r = n % 1000
        if th == 1:
            prefix = "mille"
        else:
            prefix = number_to_french(th) + " mille"

        if r == 0:
            return prefix
        return prefix + " " + number_to_french(r)

    if n < 1_000_000_000:
        m = n // 1_000_000
        r = n % 1_000_000
        if m == 1:
            prefix = "un million"
        else:
            prefix = number_to_french(m) + " millions"

        if r == 0:
            return prefix
        return prefix + " " + number_to_french(r)

    return "nombre trop grand"


def money_to_french(amount):
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_cents = int(quantized * 100)
    euros = total_cents // 100
    cents = total_cents % 100

    words = number_to_french(euros) + " dinnar"
    if euros > 1:
        words += "s"

    if cents > 0:
        words += " et " + number_to_french(cents) + " centime"
        if cents > 1:
            words += "s"

    return words


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
    converter_input = ""
    converter_result = ""
    field_values = {}

    if request.method == "POST":
        action = request.POST.get("action", "generate_print")

        for field in template.fields:
            key = field.get("key")
            if not key:
                continue
            field_values[key] = request.POST.get(key, "")

        if action == "convert_amount":
            converter_input = request.POST.get("amount_to_convert", "").strip()
            if not converter_input:
                messages.error(request, "Enter an amount to convert.")
            else:
                normalized = converter_input.replace(" ", "").replace(",", ".")
                try:
                    amount = Decimal(normalized)
                    if amount < 0:
                        messages.error(request, "Amount must be positive.")
                    elif amount >= Decimal("1000000000"):
                        messages.error(request, "Amount is too large (must be below 1,000,000,000).")
                    else:
                        converter_result = money_to_french(amount)
                except InvalidOperation:
                    messages.error(request, "Invalid number format. Example: 1234.56")
        else:
            request.session[f"template_values_{template.id}"] = field_values
            return redirect("paycheck:template_print", template_id=template.id)

    return render(
        request,
        "paycheck/template_fill.html",
        {
            "template": template,
            "field_values": field_values,
            "converter_input": converter_input,
            "converter_result": converter_result,
        },
    )


def template_print(request, template_id):
    template = get_object_or_404(CheckTemplate, id=template_id)
    values = request.session.get(f"template_values_{template.id}", {})

    def safe_float(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    if request.method == "POST":
        raw_fields = request.POST.get("fields_json")
        if raw_fields is None:
            messages.error(request, "No position data submitted.")
            return redirect("paycheck:template_print", template_id=template.id)

        try:
            parsed_fields = json.loads(raw_fields)
        except json.JSONDecodeError:
            messages.error(request, "Invalid position data. Please try again.")
            return redirect("paycheck:template_print", template_id=template.id)

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
            messages.error(request, "No field positions were saved.")
            return redirect("paycheck:template_print", template_id=template.id)

        template.fields = valid_fields
        template.save(update_fields=["fields"])
        messages.success(request, "Field positions updated.")
        return redirect("paycheck:template_print", template_id=template.id)

    return render(
        request,
        "paycheck/template_print.html",
        {
            "template": template,
            "values": values,
        },
    )
