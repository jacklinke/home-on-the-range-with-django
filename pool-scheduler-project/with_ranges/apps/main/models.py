import auto_prefetch
from apps.main.validators import (
    DateTimeRangeLowerMinuteValidator,
    DateTimeRangeMaxDurationValidator,
    DateTimeRangeMinDurationValidator,
    DateTimeRangeUpperMinuteValidator,
    validate_zeroed_dt_sec_microsec,
)
from apps.users.models import User
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import (
    DateRangeField,
    DateTimeRangeField,
    IntegerRangeField,
    RangeBoundary,
    RangeOperators,
)
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower, Upper
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from psycopg2.extras import DateRange, DateTimeRange, DateTimeTZRange, NumericRange


class PoolManager(auto_prefetch.Manager):
    def manager_only_method(self):
        return


class PoolQuerySet(auto_prefetch.QuerySet):
    def manager_and_queryset_method(self):
        return


class Pool(auto_prefetch.Model):
    """An instance of a Pool. Multiple pools may exist within the municipality"""

    name = models.CharField(_("Pool Name"), max_length=100)
    address = models.TextField(_("Address"))
    depth_range = IntegerRangeField(
        _("Depth Range"),
        help_text=_("What is the range in feet for the depth of this pool (shallow to deep)?"),
    )
    business_hours = IntegerRangeField(_("Business Hours"), default=(9, 17))

    CombinedPoolManager = PoolManager.from_queryset(PoolQuerySet)
    objects = CombinedPoolManager()

    class Meta:
        verbose_name = _("Pool")
        verbose_name_plural = _("Pools")
        ordering = ["name"]
        # ToDo: Add constraint limiting business hours and depth range

    def __str__(self):
        return self.name


class ClosureManager(auto_prefetch.Manager):
    def manager_only_method(self):
        return


class ClosureQuerySet(auto_prefetch.QuerySet):
    def manager_and_queryset_method(self):
        return


class Closure(auto_prefetch.Model):
    """A way of recording dates that a pool is closed"""

    reasons_list = [
        "Planned maintenance",
        "Boss' birthday celebration",
        "An important holiday 🎉",
        "Pool draining and refill",
        "Sinkhole opened up under pool",
        "Municipal cost measures",
        "Can't be bothered to open up 😶",
        "Filter cleaning",
        "Biohazard ☣ in pool 😬",
        "Safety inspection",
        "Repainting",
        "Penguin 🐧 infestation",
        "Locker room retrofit",
        "Repaving parking lot",
        "Too many fish in the pool",
        "Stuck at home because kitty wanted to sit on my lap 🤷",
        "Front door is broken",
        "Lost keys to the building",
        "Bake sale 🥧 - all hands needed",
        "Lifeguard has time off",
        "Forgot to pay water bill 🚱",
        "Meteor damage 🌌 - requires repair",
    ]

    pool = auto_prefetch.ForeignKey(Pool, on_delete=models.CASCADE, related_name="closures")
    dates = DateRangeField(_("Pool Closure Dates"))
    reason = models.TextField(_("Closure Reason"))

    CombinedClosureManager = ClosureManager.from_queryset(ClosureQuerySet)
    objects = CombinedClosureManager()

    class Meta:
        verbose_name = _("Closure")
        verbose_name_plural = _("Closures")
        ordering = ["pool__name"]

    def __str__(self):
        return f"{self.pool} ({self.dates.lower:%Y-%m-%d} - {self.dates.upper:%Y-%m-%d})"


class LaneManager(auto_prefetch.Manager):
    def manager_only_method(self):
        return


class LaneQuerySet(auto_prefetch.QuerySet):
    def manager_and_queryset_method(self):
        return


class Lane(models.Model):
    """Each pool may have multiple lanes, each of which can be reserved by multiple people"""

    name = models.CharField(_("Lane Name"), max_length=50)
    pool = auto_prefetch.ForeignKey(Pool, on_delete=models.CASCADE, related_name="lanes")
    max_swimmers = models.PositiveSmallIntegerField(
        _("Maximum Swimmers"),
    )
    per_hour_cost = models.DecimalField(_("Per-Hour Cost"), max_digits=5, decimal_places=2)

    CombinedLaneManager = LaneManager.from_queryset(LaneQuerySet)
    objects = CombinedLaneManager()

    class Meta:
        verbose_name = _("Lane")
        verbose_name_plural = _("Lanes")
        ordering = ["pool__name"]

    def __str__(self):
        return f"{self.pool}: {self.name}"


class LockerManager(auto_prefetch.Manager):
    def manager_only_method(self):
        return


class LockerQuerySet(auto_prefetch.QuerySet):
    def manager_and_queryset_method(self):
        return


class Locker(auto_prefetch.Model):
    """Each pool may have multiple lockers, each of which can be reserved by only one person at a time"""

    # Using CharField, because sometimes locker number might be "A23" or "56-B"
    number = models.CharField(_("Locker Number"), max_length=20)
    pool = auto_prefetch.ForeignKey(Pool, on_delete=models.CASCADE, related_name="lockers")
    per_hour_cost = models.DecimalField(_("Per-Hour Cost"), max_digits=5, decimal_places=2)

    CombinedLockerManager = LockerManager.from_queryset(LockerQuerySet)
    objects = CombinedLockerManager()

    class Meta:
        verbose_name = _("Locker")
        verbose_name_plural = _("Lockers")
        ordering = ["pool__name"]

    def __str__(self):
        return f"{self.pool}: Locker {self.number}"


class LaneReservationManager(auto_prefetch.Manager):
    def manager_only_method(self):
        return

    def get_queryset(self):
        """Return only reservations that are not cancelled"""
        return super().get_queryset().filter(cancelled__isnull=True)


class LaneReservationQuerySet(auto_prefetch.QuerySet):
    def for_pool(self, pool):
        return self.filter(lane__pool=pool)


class LaneReservation(auto_prefetch.Model):
    """A lane reservations defines a set of users, a period of time, and a pool lane"""

    users = models.ManyToManyField(User, related_name="lane_reservations")
    lane = auto_prefetch.ForeignKey(Lane, on_delete=models.CASCADE, related_name="lane_reservations")
    period = DateTimeRangeField(
        _("Reservation Period"),
        validators=[
            DateTimeRangeLowerMinuteValidator(0, 30),
            DateTimeRangeUpperMinuteValidator(0, 30),
            DateTimeRangeMinDurationValidator(timezone.timedelta(hours=9)),
            validate_zeroed_dt_sec_microsec,
        ],
    )
    actual = DateTimeRangeField(_("Actual Usage Period"), default=(None, None))
    cancelled = models.DateTimeField(_("Reservation is Cancelled"), null=True)

    CombinedLaneReservationManager = LaneReservationManager.from_queryset(LaneReservationQuerySet)
    objects = CombinedLaneReservationManager()
    all_objects = auto_prefetch.Manager()

    class Meta:
        verbose_name = _("Lane Reservation")
        verbose_name_plural = _("Lane Reservations")
        ordering = ["lane__pool__name", "period"]
        constraints = [
            # No Lane should have overlapping reservations
            ExclusionConstraint(
                name="excl_overlap_lane_res",
                expressions=[
                    ("period", RangeOperators.OVERLAPS),
                    ("lane", RangeOperators.EQUAL),
                ],
                # Ignore overlaps where the reservation is cancelled
                condition=Q(cancelled=None),
            ),
            # ToDo: No User should be included in more than one reservation at a time
            # ToDo:Reservations should have less than max number of swimmers
        ]

    def __str__(self):
        return f"{self.lane} ({self.period.lower:%Y-%m-%d %H:%M} - {self.period.upper:%Y-%m-%d %H:%M})"

    def cancel_reservation(self):
        self.cancelled = timezone.now()
        self.save(
            update_fields=[
                "cancelled",
            ]
        )
        return True

    def check_in(self):
        """Set the lower value of `actual` to now"""
        self.actual = DateTimeTZRange(timezone.now(), None)
        self.save(
            update_fields=[
                "actual",
            ]
        )
        return True

    def check_out(self):
        """Set the upper value of `actual` to now"""
        self.actual = DateTimeTZRange(self.actual.lower, timezone.now())
        self.save(
            update_fields=[
                "actual",
            ]
        )
        return True


class LockerReservationManager(auto_prefetch.Manager):
    def manager_only_method(self):
        return

    def get_queryset(self):
        """Return only reservations that are not cancelled"""
        return super().get_queryset().filter(cancelled__isnull=True)


class LockerReservationQuerySet(auto_prefetch.QuerySet):
    def for_pool(self, pool):
        return self.filter(locker__pool=pool)


class LockerReservation(auto_prefetch.Model):
    """A locker reservation defines a user, a period of time, and a pool locker"""

    user = auto_prefetch.ForeignKey(User, on_delete=models.CASCADE, related_name="locker_reservations")
    locker = auto_prefetch.ForeignKey(Locker, on_delete=models.CASCADE, related_name="locker_reservations")
    period = DateTimeRangeField(
        _("Reservation Period"),
        validators=[
            DateTimeRangeLowerMinuteValidator(0, 30),
            DateTimeRangeUpperMinuteValidator(0, 30),
            DateTimeRangeMaxDurationValidator(timezone.timedelta(days=20)),
            validate_zeroed_dt_sec_microsec,
        ],
    )
    actual = DateTimeRangeField(_("Actual Usage Period"), default=(None, None))
    cancelled = models.DateTimeField(_("Reservation is Cancelled"), null=True)

    CombinedLockerReservationManager = LockerReservationManager.from_queryset(LockerReservationQuerySet)
    objects = CombinedLockerReservationManager()
    all_objects = auto_prefetch.Manager()

    class Meta:
        verbose_name = _("Locker Reservation")
        verbose_name_plural = _("Locker Reservations")
        ordering = ["locker__pool__name", "period"]
        constraints = [
            # No Locker should have overlapping reservations
            ExclusionConstraint(
                name="excl_overlap_locker_res",
                expressions=[
                    ("period", RangeOperators.OVERLAPS),
                    ("locker", RangeOperators.EQUAL),
                ],
                # Ignore overlaps where the reservation is cancelled
                condition=Q(cancelled=None),
            ),
            # No User should have more than one reservation at a time
            ExclusionConstraint(
                name="excl_overlap_user_locker_res",
                expressions=[
                    ("period", RangeOperators.OVERLAPS),
                    ("user", RangeOperators.EQUAL),
                ],
                # Ignore overlaps where the reservation is cancelled
                condition=Q(cancelled=None),
            ),
        ]

    def __str__(self):
        return f"{self.locker} ({self.period.lower:%Y-%m-%d %H:%M} - {self.period.upper:%Y-%m-%d %H:%M})"

    def cancel_reservation(self):
        self.cancelled = timezone.now()
        self.save(
            update_fields=[
                "cancelled",
            ]
        )
        return True

    def check_in(self):
        """Set the lower value of `actual` to now"""
        self.actual = DateTimeTZRange(timezone.now(), None)
        self.save(
            update_fields=[
                "actual",
            ]
        )
        return True

    def check_out(self):
        """Set the upper value of `actual` to now"""
        self.actual = DateTimeTZRange(self.actual.lower, timezone.now())
        self.save(
            update_fields=[
                "actual",
            ]
        )
        return True
