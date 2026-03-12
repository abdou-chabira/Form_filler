from django.urls import path

from . import views

app_name = "paycheck"

urlpatterns = [
    path("", views.template_list, name="template_list"),
    path("templates/new/", views.template_create, name="template_create"),
    path("templates/<int:template_id>/design/", views.template_design, name="template_design"),
    path("templates/<int:template_id>/fill/", views.template_fill, name="template_fill"),
    path("templates/<int:template_id>/print/", views.template_print, name="template_print"),
]
