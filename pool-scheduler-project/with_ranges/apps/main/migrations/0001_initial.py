# Generated by Django 4.1.2 on 2022-10-19 21:33

import datetime

import apps.main.validators
import auto_prefetch
import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.db.models.deletion
import django.db.models.manager
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Lane",
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
                ("name", models.CharField(max_length=50, verbose_name="Lane Name")),
                (
                    "max_swimmers",
                    models.PositiveSmallIntegerField(verbose_name="Maximum Swimmers"),
                ),
                (
                    "per_hour_cost",
                    models.DecimalField(decimal_places=2, max_digits=5, verbose_name="Per-Hour Cost"),
                ),
            ],
            options={
                "verbose_name": "Lane",
                "verbose_name_plural": "Lanes",
                "ordering": ["pool__name"],
            },
        ),
        migrations.CreateModel(
            name="Locker",
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
                (
                    "number",
                    models.CharField(max_length=20, verbose_name="Locker Number"),
                ),
                (
                    "per_hour_cost",
                    models.DecimalField(decimal_places=2, max_digits=5, verbose_name="Per-Hour Cost"),
                ),
            ],
            options={
                "verbose_name": "Locker",
                "verbose_name_plural": "Lockers",
                "ordering": ["pool__name"],
            },
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="Pool",
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
                ("name", models.CharField(max_length=100, verbose_name="Pool Name")),
                ("address", models.TextField(verbose_name="Address")),
                (
                    "depth_range",
                    django.contrib.postgres.fields.ranges.IntegerRangeField(
                        help_text="What is the range in feet for the depth of this pool (shallow to deep)?",
                        verbose_name="Depth Range",
                    ),
                ),
                (
                    "business_hours",
                    django.contrib.postgres.fields.ranges.IntegerRangeField(
                        default=(9, 17), verbose_name="Business Hours"
                    ),
                ),
            ],
            options={
                "verbose_name": "Pool",
                "verbose_name_plural": "Pools",
                "ordering": ["name"],
            },
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="LockerReservation",
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
                (
                    "period",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        validators=[
                            apps.main.validators.DateTimeRangeLowerMinuteValidator(0, 30),
                            apps.main.validators.DateTimeRangeUpperMinuteValidator(0, 30),
                            apps.main.validators.DateTimeRangeMaxDurationValidator(datetime.timedelta(days=20)),
                            apps.main.validators.validate_zeroed_dt_sec_microsec,
                        ],
                        verbose_name="Reservation Period",
                    ),
                ),
                (
                    "actual",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        default=(None, None), verbose_name="Actual Usage Period"
                    ),
                ),
                (
                    "cancelled",
                    models.DateTimeField(null=True, verbose_name="Reservation is Cancelled"),
                ),
                (
                    "locker",
                    auto_prefetch.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="locker_reservations",
                        to="main.locker",
                    ),
                ),
                (
                    "user",
                    auto_prefetch.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="locker_reservations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Locker Reservation",
                "verbose_name_plural": "Locker Reservations",
                "ordering": ["locker__pool__name", "period"],
            },
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name="locker",
            name="pool",
            field=auto_prefetch.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lockers",
                to="main.pool",
            ),
        ),
        migrations.CreateModel(
            name="LaneReservation",
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
                (
                    "period",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        validators=[
                            apps.main.validators.DateTimeRangeLowerMinuteValidator(0, 30),
                            apps.main.validators.DateTimeRangeUpperMinuteValidator(0, 30),
                            apps.main.validators.DateTimeRangeMinDurationValidator(datetime.timedelta(seconds=32400)),
                            apps.main.validators.validate_zeroed_dt_sec_microsec,
                        ],
                        verbose_name="Reservation Period",
                    ),
                ),
                (
                    "actual",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        default=(None, None), verbose_name="Actual Usage Period"
                    ),
                ),
                (
                    "cancelled",
                    models.DateTimeField(null=True, verbose_name="Reservation is Cancelled"),
                ),
                (
                    "lane",
                    auto_prefetch.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lane_reservations",
                        to="main.lane",
                    ),
                ),
                (
                    "users",
                    models.ManyToManyField(related_name="lane_reservations", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "verbose_name": "Lane Reservation",
                "verbose_name_plural": "Lane Reservations",
                "ordering": ["lane__pool__name", "period"],
            },
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name="lane",
            name="pool",
            field=auto_prefetch.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lanes",
                to="main.pool",
            ),
        ),
        migrations.CreateModel(
            name="Closure",
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
                (
                    "dates",
                    django.contrib.postgres.fields.ranges.DateRangeField(verbose_name="Pool Closure Dates"),
                ),
                ("reason", models.TextField(verbose_name="Closure Reason")),
                (
                    "pool",
                    auto_prefetch.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="closures",
                        to="main.pool",
                    ),
                ),
            ],
            options={
                "verbose_name": "Closure",
                "verbose_name_plural": "Closures",
                "ordering": ["pool__name"],
            },
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddConstraint(
            model_name="lockerreservation",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                condition=models.Q(("cancelled", None)),
                expressions=[("period", "&&"), ("locker", "=")],
                name="excl_overlap_locker_res",
            ),
        ),
        migrations.AddConstraint(
            model_name="lockerreservation",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                condition=models.Q(("cancelled", None)),
                expressions=[("period", "&&"), ("user", "=")],
                name="excl_overlap_user_locker_res",
            ),
        ),
        migrations.AddConstraint(
            model_name="lanereservation",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                condition=models.Q(("cancelled", None)),
                expressions=[("period", "&&"), ("lane", "=")],
                name="excl_overlap_lane_res",
            ),
        ),
    ]