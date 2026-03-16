from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import CheckTemplate


@admin.register(CheckTemplate)
class CheckTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "width_mm", "height_mm", "field_count", "edit_fonts", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/font-sizes/",
                self.admin_site.admin_view(self.font_sizes_view),
                name="paycheck_checktemplate_font_sizes",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Font Sizes")
    def edit_fonts(self, obj):
        url = reverse("admin:paycheck_checktemplate_font_sizes", args=[obj.pk])
        return format_html('<a href="{}">Edit font_size_mm</a>', url)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["font_sizes_url"] = reverse("admin:paycheck_checktemplate_font_sizes", args=[object_id])
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def font_sizes_view(self, request, object_id):
        obj = get_object_or_404(CheckTemplate, pk=object_id)

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        fields = obj.fields if isinstance(obj.fields, list) else []

        if request.method == "POST":
            updated_fields = []
            had_error = False
            for index, field in enumerate(fields):
                if not isinstance(field, dict):
                    continue

                raw_font_size = request.POST.get(f"font_size_mm_{index}", "").strip()
                try:
                    font_size = float(raw_font_size)
                except (TypeError, ValueError):
                    messages.error(request, f"Invalid font_size_mm for field #{index + 1}.")
                    had_error = True
                    break

                field_copy = dict(field)
                field_copy["font_size_mm"] = max(1.5, min(12, font_size))
                updated_fields.append(field_copy)

            if not had_error:
                obj.fields = updated_fields
                obj.save(update_fields=["fields"])
                messages.success(request, "font_size_mm values updated.")
                return redirect("admin:paycheck_checktemplate_change", object_id=obj.pk)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": obj,
            "title": f"Edit font_size_mm: {obj}",
            "fields": fields,
            "change_url": reverse("admin:paycheck_checktemplate_change", args=[obj.pk]),
        }
        return TemplateResponse(request, "admin/paycheck/checktemplate/font_sizes.html", context)

    @admin.display(description="Fields")
    def field_count(self, obj):
        if isinstance(obj.fields, list):
            return len(obj.fields)
        return 0
