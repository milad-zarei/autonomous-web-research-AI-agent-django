import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ResearchJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Waiting"),
                            ("running", "Running"),
                            ("done", "Done"),
                            ("error", "Failed"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("log", models.TextField(blank=True)),
                ("answer", models.TextField(blank=True)),
                ("error", models.TextField(blank=True)),
                ("pdf_path", models.CharField(blank=True, max_length=500)),
                ("docx_path", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="research_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
