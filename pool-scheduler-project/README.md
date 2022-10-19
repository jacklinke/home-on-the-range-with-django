# Home on the range with Django - Getting comfortable with ranges and range fields


## Demonstration Project

This project is a work-in-progress

In order to demonstrate the different approaches to working with range data, it is helpful to have a concrete example to play with. Here we have chosen to build a simple application for managing the swimming pools within a municipality.

![database schema simple](https://raw.githubusercontent.com/jacklinke/home-on-the-range-with-django/master/presentation/img/erd_light.png)

![database schema detailed](https://raw.githubusercontent.com/jacklinke/home-on-the-range-with-django/master/presentation/img/erd.png)


## Pool Scheduling Project Description

The local municipality has commissioned us to build a scheduling tool that will allow customers to make reservations for their public swimming pools.

In order to do this, we have set up some arbitrary goals and business rules for scheduling, in order to demonstrate a number of different examples when it comes to working with ranges.

* There may be more than one `Pool` within the municipality.
* Each `Lane` within a `Pool` has a person-limit - the maximum number of people who can swim in that lane at a given moment.
* Each `Lane` within a `Pool` can be reserved for use by one or more people in a `Party`, but the total number of people must not exceed the lane's person-limit at any time.
* A `Locker` can be assigned to only one person at a time (no overlapping `LockerReservation` allowed).
* In this example, to keep things somewhat simple, we will assume all `Pool`, `Lane`, and `Locker` are always open. Once you have completed this series, adding 'closed' periods should be relatively simple.
* We will add basic per-hour pricing, which will require some intermediate/advanced querying. If a resource (`Lane` or `Locker`) is reserved less than an hour, we will simply multiply the time reserved by the per-hour pricing for 1 hour.


## Running the Demos

Demonstrations of the pool scheduling project are available in this repository. A django project with ranges are included to allow for comparison in approaches.

*Note: This project uses Docker Compose V2. Installation instructions can be found [here](https://docs.docker.com/compose/install/).*


### Build and Run Projects

```shell
docker compose build
docker compose up -d
docker compose run django python manage.py migrate
```

The project can then be accessed at [127.0.0.1:8002](http://127.0.0.1:8002/)

### Admin

The Admin is not fully built-out yet, but you can currently view and edit each model using the default widgets.


```shell
docker compose run django python manage.py createsuperuser
```

Then visit [127.0.0.1:8002](http://127.0.0.1:8002/admin/) to log in.


### Django Commands

#### Mock some demo data

```shell
docker compose run django python manage.py mock_data
```

![Screensht of data mocking](https://raw.githubusercontent.com/jacklinke/home-on-the-range-with-django/master/presentation/img/Screenshot%20from%202022-10-19%2014-34-27.png)

#### Delete all model instances

```shell
docker compose run django python manage.py delete_data
```



### Check that it worked

with: http://127.0.0.1:8002



### Completely Remove the Project Containers and Volumes

```shell
docker compose down --rmi all --remove-orphans -v
```


### Stripped-down Original models.py

```python
from django.db import models
from django.db.models import Q, Func
from apps.users.models import User

from django.contrib.postgres.fields import (
    DateRangeField,
    IntegerRangeField,
    DateTimeRangeField,
    RangeBoundary,
    RangeOperators,
)
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.constraints import ExclusionConstraint


class TsTzRange(Func):
    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()
    
    
class Pool(models.Model):
    """An instance of a Pool. Multiple pools may exist within the municipality"""

    name = models.CharField(_("Pool Name"), max_length=100)
    address = models.TextField(_("Address"))
    depth_minimum = models.IntegerField(
        _("Depth Minimum"),
        help_text=_("What is the depth in feet of the shallow end of this pool?"),
    )
    depth_maximum = models.IntegerField(
        _("Depth Maximum"),
        help_text=_("What is the depth in feet of the deep end of this pool?"),
    )


class Closure(models.Model):
    """A way of recording dates that a pool is closed"""

    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name="closures")
    start_date = models.DateField(_("Pool Closure Start Date"))
    end_date = models.DateField(_("Pool Closure End Date"))
    reason = models.TextField(_("Closure Reason"))


class Lane(models.Model):
    """Each pool may have multiple lanes, each of which can be reserved by multiple people"""

    name = models.CharField(_("Lane Name"), max_length=50)
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name="lanes")
    max_swimmers = models.PositiveSmallIntegerField(
        _("Maximum Swimmers"),
    )
    per_hour_cost = models.DecimalField(_("Per-Hour Cost"), max_digits=5, decimal_places=2)


class Locker(models.Model):
    """Each pool may have multiple lockers, each of which can be reserved by only one person at a time"""

    # Using CharField, because sometimes locker number might be "A23" or "56-B"
    number = models.CharField(_("Locker Number"), max_length=20)
    pool = models.ForeignKey(Pool, on_delete=models.CASCADE, related_name="lockers")
    per_hour_cost = models.DecimalField(_("Per-Hour Cost"), max_digits=5, decimal_places=2)


class LaneReservation(models.Model):
    """A lane reservations defines a set of users, a period of time, and a pool lane"""

    users = models.ManyToManyField(User, related_name="lane_reservations")
    lane = models.ForeignKey(Lane, on_delete=models.CASCADE, related_name="lane_reservations")
    period_start = models.DateTimeField(_("Reservation Period Start"))
    period_end = models.DateTimeField(_("Reservation Period End"))

    class Meta:
        constraints = [
            # No Locker should have overlapping reservations
            ExclusionConstraint(
                name="excl_overlap_lane_res",
                expressions=(
                    (TsTzRange("period_start", "period_end", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("lane", RangeOperators.EQUAL),
                ),
                condition=Q(cancelled=False),
            ),
            # ToDo: No User should be included in more than one reservation at a time
        ]


class LockerReservation(models.Model):
    """A locker reservation defines a user, a period of time, and a pool locker"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="locker_reservations")
    locker = models.ForeignKey(Locker, on_delete=models.CASCADE, related_name="locker_reservations")
    period_start = models.DateTimeField(_("Reservation Period Start"))
    period_end = models.DateTimeField(_("Reservation Period End"))

    class Meta:
        constraints = [
            # No Locker should have overlapping reservations
            ExclusionConstraint(
                name="excl_overlap_locker_res",
                expressions=(
                    (TsTzRange("period_start", "period_end", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("locker", RangeOperators.EQUAL),
                ),
                condition=Q(cancelled=False),
            ),
            # ToDo: No User should be included in more than one reservation at a time
        ]
```

### Stripped-down final models.py

```python
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


class Pool(auto_prefetch.Model):
    """An instance of a Pool. Multiple pools may exist within the municipality"""

    name = models.CharField(_("Pool Name"), max_length=100)
    address = models.TextField(_("Address"))
    depth_range = IntegerRangeField(
        _("Depth Range"),
        help_text=_("What is the range in feet for the depth of this pool (shallow to deep)?"),
    )
    business_hours = IntegerRangeField(_("Business Hours"), default=(9, 17))


class Closure(auto_prefetch.Model):
    """A way of recording dates that a pool is closed"""

    pool = auto_prefetch.ForeignKey(Pool, on_delete=models.CASCADE, related_name="closures")
    dates = DateRangeField(_("Pool Closure Dates"))
    reason = models.TextField(_("Closure Reason"))


class Lane(models.Model):
    """Each pool may have multiple lanes, each of which can be reserved by multiple people"""

    name = models.CharField(_("Lane Name"), max_length=50)
    pool = auto_prefetch.ForeignKey(Pool, on_delete=models.CASCADE, related_name="lanes")
    max_swimmers = models.PositiveSmallIntegerField(
        _("Maximum Swimmers"),
    )
    per_hour_cost = models.DecimalField(_("Per-Hour Cost"), max_digits=5, decimal_places=2)


class Locker(auto_prefetch.Model):
    """Each pool may have multiple lockers, each of which can be reserved by only one person at a time"""

    # Using CharField, because sometimes locker number might be "A23" or "56-B"
    number = models.CharField(_("Locker Number"), max_length=20)
    pool = auto_prefetch.ForeignKey(Pool, on_delete=models.CASCADE, related_name="lockers")
    per_hour_cost = models.DecimalField(_("Per-Hour Cost"), max_digits=5, decimal_places=2)


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

    class Meta:
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

    class Meta:
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
```


### Template

This project uses [Start Bootstrap's Simple Sidebar template](https://github.com/startbootstrap/startbootstrap-simple-sidebar) with Bootstrap 5 in order to provide a decent-looking but very simple foundation for the demonstration.
