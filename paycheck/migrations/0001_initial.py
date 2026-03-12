from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CheckTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("image", models.ImageField(upload_to="checks/")),
                ("width_mm", models.DecimalField(decimal_places=2, max_digits=7)),
                ("height_mm", models.DecimalField(decimal_places=2, max_digits=7)),
                ("fields", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
