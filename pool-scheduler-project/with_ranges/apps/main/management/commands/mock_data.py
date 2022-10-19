import random
import sys
from datetime import time

from apps.main.models import (
    Closure,
    Lane,
    LaneReservation,
    Locker,
    LockerReservation,
    Pool,
)
from apps.users.models import User
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.utils import timezone
from faker import Faker
from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange

fake = Faker()


class Command(BaseCommand):
    help = "Generates mock data for user, device"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            "######################################### Generate Example Data #########################################"
        )

        self.stdout.write("\n")

        start_date_value = timezone.datetime.today() - timezone.timedelta(days=30)
        end_date_value = timezone.datetime.today() + timezone.timedelta(days=90)
        today_date_string = start_date_value.strftime("%Y%m%d")
        later_date_string = end_date_value.strftime("%Y%m%d")

        try:
            number_of_users = input("Enter the number of users to include in the app (default: 50): ") or 50
            number_of_users = int(number_of_users)

            number_of_pools = input("Enter the number of pools in the municipality (default: 10): ") or 10
            number_of_pools = int(number_of_pools)

            minimum_lanes = input("Enter the minimum number of lanes in a pool (default: 1): ") or 1
            minimum_lanes = int(minimum_lanes)

            maximum_lanes = input("Enter the maximum number of lanes in a pool (default: 5): ") or 5
            maximum_lanes = int(maximum_lanes)

            start_date = (
                input(f"Enter the start date for the example data [YYYYMMDD] (default: {today_date_string}): ")
                or today_date_string
            )
            start_date = str(start_date)

            end_date = (
                input(f"Enter the end date for the example data [YYYYMMDD] (default: {later_date_string}): ")
                or later_date_string
            )
            end_date = str(end_date)

            start_date_value = timezone.datetime.strptime(start_date, "%Y%m%d").date()
            end_date_value = timezone.datetime.strptime(end_date, "%Y%m%d").date()
            if not start_date_value < end_date_value:
                raise ValueError(f"Start Date ({start_date}) must be smaller than End Date ({end_date})")

        except ValueError as e:
            self.stdout.write(e)
            sys.exit()

        # Generate Users
        user_email_list = list(set([fake.ascii_free_email() for i in range(1, number_of_users + 1)]))
        user_instances = []
        for email in user_email_list:
            is_staff = random.randrange(0, 15) == 0

            user_obj = User(email=email, is_staff=is_staff, first_name=fake.first_name(), last_name=fake.last_name())
            user_instances.append(user_obj)
        User.objects.bulk_create(user_instances)

        self.stdout.write("\n")
        self.stdout.write("Users created....")

        # Generate Pools
        pool_instances = []
        for i in range(1, number_of_pools + 1):
            name = f"{fake.company()} Pool"
            address = fake.address()
            depth_range_value = sorted([random.randrange(3, 5), random.randrange(6, 18)])
            depth_range = NumericRange(*depth_range_value)
            business_hours = (random.randrange(5, 13), random.randrange(16, 19))

            pool_obj = Pool(
                name=name,
                address=address,
                depth_range=depth_range,
                business_hours=business_hours,
            )
            pool_instances.append(pool_obj)
        Pool.objects.bulk_create(pool_instances)

        self.stdout.write("\n")
        self.stdout.write("Pools created....")

        # Generate Lanes for each Pool
        lane_instances = []
        for pool in Pool.objects.all():
            for i in range(random.randrange(minimum_lanes, maximum_lanes + 1)):
                name = f"Lane {i}"
                max_swimmers = random.randrange(1, 11)
                per_hour_cost = round(random.uniform(2.00, 20.00), 2)

                lane_object = Lane(
                    pool=pool,
                    name=name,
                    max_swimmers=max_swimmers,
                    per_hour_cost=per_hour_cost,
                )
                lane_instances.append(lane_object)
        Lane.objects.bulk_create(lane_instances)

        self.stdout.write("\n")
        self.stdout.write("Lanes created....")

        # Generate a random number of lockers for each Pool
        locker_instances = []
        for pool in Pool.objects.all():
            for i in range(random.randrange(11, 61)):
                number = i + 1
                per_hour_cost = round(random.uniform(2.00, 20.00), 2)

                locker_object = Locker(pool=pool, number=number, per_hour_cost=per_hour_cost)
                locker_instances.append(locker_object)
        Locker.objects.bulk_create(locker_instances)

        self.stdout.write("\n")
        self.stdout.write("Lockers created....")

        def get_random_date_range():
            """Returns a random instance of psycopg2.extras DateRange"""
            length_in_days = random.randrange(1, 8)

            duration_between_dates = end_date_value - start_date_value
            days_between_dates = duration_between_dates.days
            random_number_of_days_from_start = random.randrange(days_between_dates)
            random_start = start_date_value + timezone.timedelta(days=random_number_of_days_from_start)
            random_end = random_start + timezone.timedelta(days=length_in_days)

            random_date_range = sorted([random_start, random_end])
            return DateRange(random_date_range[0], random_date_range[1])

        def get_random_int_range_in_range(outer_range):
            """
            Given an integer range, returns another integer range fully contained within the first.
                Useful for returning a range of time within business hours.

            Example:

                `new_range = get_random_int_range_in_range(outer_range=NumericRange(9, 17))`

            """
            random_lower = random.randrange(outer_range.lower, outer_range.upper)
            random_upper = random.randrange(random_lower + 1, outer_range.upper + 1)
            return NumericRange(random_lower, random_upper)

        def get_lane_reservation_range(pool_for_reservation):
            """
            Given a Pool instance, returns a DateTimeTZRange within business hours on a random date
            """
            reservation_hours = get_random_int_range_in_range(pool_for_reservation.business_hours)
            days_between_dates = (end_date_value - start_date_value).days
            random_number_of_days_from_start = random.randrange(days_between_dates)
            reservation_date = start_date_value + timezone.timedelta(days=random_number_of_days_from_start)

            reservation_date_lower = timezone.datetime.combine(reservation_date, time(hour=reservation_hours.lower))
            reservation_date_upper = timezone.datetime.combine(reservation_date, time(hour=reservation_hours.upper))

            return DateTimeTZRange(reservation_date_lower, reservation_date_upper)

        def get_locker_reservation_range(pool_for_reservation):
            """
            Given a Pool instance, returns a DateTimeTZRange from business hours lower value of one date to business
                hours upper value of a later date
            """
            days_between_dates = (end_date_value - start_date_value).days
            random_number_of_days_from_start = random.randrange(days_between_dates)
            reservation_date_start = start_date_value + timezone.timedelta(days=random_number_of_days_from_start)

            random_number_of_days_from_reservation_start = random.randrange(
                (end_date_value - reservation_date_start).days
            )
            reservation_date_end = reservation_date_start + timezone.timedelta(
                days=random_number_of_days_from_reservation_start
            )

            reservation_date_lower = timezone.datetime.combine(
                reservation_date_start, time(hour=pool_for_reservation.business_hours.lower)
            )
            reservation_date_upper = timezone.datetime.combine(
                reservation_date_end, time(hour=pool_for_reservation.business_hours.upper)
            )

            return DateTimeTZRange(reservation_date_lower, reservation_date_upper)

        def get_random_users(max_users=10):
            """Returns a queryset of random Users"""
            full_user_id_list = list(User.objects.all().values_list("id", flat=True))
            random_user_id_list = []
            user_list_amount = random.randrange(1, max_users + 1)
            for i in range(user_list_amount):
                random_user_id_list.append(random.choice(full_user_id_list))
            user_set = User.objects.filter(id__in=random_user_id_list)

            return user_set

        def get_random_user():
            """Returns a queryset of random Users"""
            full_user_id_list = list(User.objects.all().values_list("id", flat=True))
            return User.objects.get(id=random.choice(full_user_id_list))

        # Generate 5 random Closures per Pool
        closure_instances = []
        for pool in Pool.objects.all():
            for i in range(5):
                reason = random.choice(Closure.reasons_list)
                dates = get_random_date_range()

                closure_object = Closure(pool=pool, reason=reason, dates=dates)
                closure_instances.append(closure_object)
        Closure.objects.bulk_create(closure_instances)

        self.stdout.write("\n")
        self.stdout.write("Closures created....")

        # Generate 5 LaneReservations per Lane
        for lane in Lane.objects.all():
            for i in range(5):
                period = get_lane_reservation_range(pool_for_reservation=lane.pool)

                if (rand_actual := random.randrange(0, 10)) == 8:
                    actual = DateTimeTZRange(None, None)
                elif rand_actual == 9:
                    actual = DateTimeTZRange(period.lower, None)
                else:
                    actual = period

                try:
                    lane_reservation_object = LaneReservation.objects.create(lane=lane, period=period, actual=actual)
                except IntegrityError:
                    pass
                else:
                    users = get_random_users(lane.max_swimmers)
                    lane_reservation_object.users.add(*users)
                    lane_reservation_object.save()

        self.stdout.write("\n")
        self.stdout.write("Lane Reservations created....")

        # Attempts to generate 5 LockerReservations per Locker, but fewer will be generated since there will be overlaps
        for locker in Locker.objects.all():
            for i in range(3):
                user = get_random_user()
                period = get_locker_reservation_range(pool_for_reservation=locker.pool)

                try:
                    LockerReservation.objects.create(locker=locker, user=user, period=period)
                except IntegrityError:
                    pass

        self.stdout.write("\n")
        self.stdout.write("Locker Reservations created....")

        self.stdout.write("**** Model Instance Records ****")
        self.stdout.write(f"Total Users: {User.objects.count()}")
        self.stdout.write(f"Total Pools: {Pool.objects.count()}")
        self.stdout.write(f"Total Lanes: {Lane.objects.count()}")
        self.stdout.write(f"Total Lockers: {Locker.objects.count()}")
        self.stdout.write(f"Total Closures: {Closure.objects.count()}")
        self.stdout.write(f"Total Lane Reservations: {LaneReservation.objects.count()}")
        self.stdout.write(f"Total Locker Reservations: {LockerReservation.objects.count()}")
