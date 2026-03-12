from django.contrib import admin

from .models import CheckTemplate


@admin.register(CheckTemplate)
class CheckTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "width_mm", "height_mm", "field_count", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    @admin.display(description="Fields")
    def field_count(self, obj):
        if isinstance(obj.fields, list):
            return len(obj.fields)
        return 0
