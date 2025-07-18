# Generated by Django 3.2.23 on 2025-06-25 02:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FuelStation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("opis_id", models.IntegerField(db_index=True, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("city", models.CharField(db_index=True, max_length=100)),
                ("state", models.CharField(db_index=True, max_length=2)),
                (
                    "retail_price",
                    models.DecimalField(
                        decimal_places=3,
                        max_digits=6,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
                ("latitude", models.DecimalField(decimal_places=7, max_digits=10)),
                ("longitude", models.DecimalField(decimal_places=7, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddIndex(
            model_name="fuelstation",
            index=models.Index(
                fields=["latitude", "longitude"], name="fuel_optimi_latitud_cbced2_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="fuelstation",
            index=models.Index(
                fields=["retail_price"], name="fuel_optimi_retail__913dd9_idx"
            ),
        ),
    ]
