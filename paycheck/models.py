from django.db import models


class CheckTemplate(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to="checks/")
    width_mm = models.DecimalField(max_digits=7, decimal_places=2)
    height_mm = models.DecimalField(max_digits=7, decimal_places=2)
    fields = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
