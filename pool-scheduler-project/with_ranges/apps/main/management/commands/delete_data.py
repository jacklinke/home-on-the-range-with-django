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
from faker import Faker

fake = Faker()


class Command(BaseCommand):
    help = "Deletes all data except Staff Users"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            "######################################### Delete Example Data #########################################"
        )

        self.stdout.write("\n")

        self.stdout.write("**** Preparing to Delete Records ****")
        self.stdout.write(f"Total Users to Delete: {User.objects.count()}")
        self.stdout.write(f"Total Pools to Delete: {Pool.objects.count()}")
        self.stdout.write(f"Total Lanes to Delete: {Lane.objects.count()}")
        self.stdout.write(f"Total Closure to Delete: {Closure.objects.count()}")
        self.stdout.write(f"Total Lockers to Delete: {Locker.objects.count()}")
        self.stdout.write(f"Total Lane Reservations to Delete: {LaneReservation.objects.count()}")
        self.stdout.write(f"Total Locker Reservations to Delete: {LockerReservation.objects.count()}")

        try:
            confirm_delete = input("Are you sure you want to delete all data? [yes/no] (default: no): ") or "no"
            confirm_delete = str(confirm_delete)

            if confirm_delete == "yes":
                LockerReservation.all_objects.all().delete()
                LaneReservation.all_objects.all().delete()
                Locker.objects.all().delete()
                Closure.objects.all().delete()
                Lane.objects.all().delete()
                Pool.objects.all().delete()
                User.objects.exclude(is_staff=True).delete()

                self.stdout.write("**** Deleted Records ****")
                self.stdout.write(f"Remaining Users: {User.objects.count()}")
                self.stdout.write(f"Remaining Pools: {Pool.objects.count()}")
                self.stdout.write(f"Remaining Lanes: {Lane.objects.count()}")
                self.stdout.write(f"Remaining Lanes: {Closure.objects.count()}")
                self.stdout.write(f"Remaining Lanes: {Locker.objects.count()}")
                self.stdout.write(f"Remaining Lanes: {LaneReservation.objects.count()}")
                self.stdout.write(f"Remaining Lanes: {LockerReservation.objects.count()}")

            else:
                self.stdout.write("User did not enter 'yes'. Canceling data deletion.")

        except ValueError as e:
            self.stdout.write(e)
            # sys.exit()
