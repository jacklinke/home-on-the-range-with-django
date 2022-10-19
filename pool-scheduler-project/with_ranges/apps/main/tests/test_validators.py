import unittest

from apps.main.validators import (
    DateTimeRangeLowerMinuteValidator,
    DateTimeRangeUpperMinuteValidator,
    validate_zeroed_dt_sec_microsec,
)
from django.core import exceptions
from django.db import connection
from django.test import SimpleTestCase
from django.utils import timezone
from psycopg2.extras import DateRange, DateTimeRange, DateTimeTZRange, NumericRange


@unittest.skipUnless(connection.vendor == "postgresql", "PostgreSQL specific tests")
class PostgreSQLSimpleTestCase(SimpleTestCase):
    pass


class TestValidators(PostgreSQLSimpleTestCase):
    def setUp(self):
        super().setUp()
        self.bad_dt = timezone.datetime(year=2031, month=1, day=1, hour=1, minute=0, second=1, microsecond=1)
        self.dt_0 = timezone.datetime(year=2031, month=1, day=1, hour=1, minute=0)
        self.dt_5 = timezone.datetime(year=2031, month=1, day=1, hour=1, minute=5)
        self.dt_10 = timezone.datetime(year=2031, month=1, day=1, hour=1, minute=10)
        self.dt_15 = timezone.datetime(year=2031, month=1, day=1, hour=1, minute=15)

    def test_max(self):
        validator = DateTimeRangeUpperMinuteValidator(
            [
                5,
            ]
        )
        validator(DateTimeRange(self.dt_0, self.dt_5))

        msg = "Ensure that the upper bound of the range is in [5]."
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator(DateTimeRange(self.dt_0, self.dt_10))
        self.assertEqual(cm.exception.messages[0], msg)
        self.assertEqual(cm.exception.code, "max_value")
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            validator(DateTimeRange(self.dt_0, None))  # an unbound range

    def test_min(self):
        validator = DateTimeRangeLowerMinuteValidator(
            [
                5,
            ]
        )
        validator(DateTimeRange(self.dt_5, self.dt_15))

        msg = "Ensure that the lower bound of the range is in [5]."
        with self.assertRaises(exceptions.ValidationError) as cm:
            validator(DateTimeRange(self.dt_0, self.dt_10))
        self.assertEqual(cm.exception.messages[0], msg)
        self.assertEqual(cm.exception.code, "min_value")
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            validator(DateTimeRange(None, self.dt_10))  # an unbound range

    def test_validate_zeroed_dt_sec_microsec(self):
        validate_zeroed_dt_sec_microsec(DateTimeRange(self.dt_5, self.dt_15))
        msg = (
            "Seconds and Microseconds for [2031-01-01 01:00:01.000001, 2031-01-01 01:00:01.000001) "
            "are not zeroed out."
        )
        with self.assertRaises(exceptions.ValidationError) as cm:
            validate_zeroed_dt_sec_microsec(DateTimeRange(self.bad_dt, self.bad_dt))
        self.assertEqual(cm.exception.messages[0], msg)
        self.assertEqual(cm.exception.code, "validate_zeroed")
