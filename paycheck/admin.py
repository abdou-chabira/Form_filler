from django.contrib import admin

from .models import CheckTemplate


@admin.register(CheckTemplate)
class CheckTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "width_mm", "height_mm", "created_at")
    search_fields = ("name",)
