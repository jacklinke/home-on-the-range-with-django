from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator


class DateTimeRangeUpperMinuteValidator(MaxValueValidator):
    """
    Given a list of integer minute values (e.g.: [0, 30]) validation fails if a.upper is missing,
        or if a is not in the limit_value list
    """

    def compare(self, a, b):
        if isinstance(b, int):
            b = list(
                [
                    b,
                ]
            )
        return a.upper is None or a.upper.minute not in b

    message = "Ensure that the upper bound of the range is in %(limit_value)s."


class DateTimeRangeLowerMinuteValidator(MinValueValidator):
    """
    Given a list of integer minute values (e.g.: [0, 30]) validation fails if a.lower is missing,
        or if a is not in the limit_value list
    """

    def compare(self, a, b):
        if isinstance(b, int):
            b = list(
                [
                    b,
                ]
            )
        return a.lower is None or a.lower.minute not in b

    message = "Ensure that the lower bound of the range is in %(limit_value)s."


class DateTimeRangeMinDurationValidator(MinValueValidator):
    """
    Given a datetime.timedelta object, ensures the DateTimeRangeField duration is greater than or equal in length
    """

    def compare(self, a, b):

        return a.upper - a.lower >= b

    message = "Ensure that the duration is greater than or equal to %(limit_value)s."


class DateTimeRangeMaxDurationValidator(MinValueValidator):
    """
    Given a datetime.timedelta object, ensures the DateTimeRangeField duration is less than or equal in length
    """

    def compare(self, a, b):

        return a.upper - a.lower <= b

    message = "Ensure that the duration is less than or equal to %(limit_value)s."


def validate_zeroed_dt_sec_microsec(value):
    if (
        value.lower.second != 0
        or value.lower.microsecond != 0
        or value.upper.second != 0
        or value.upper.microsecond != 0
    ):
        raise ValidationError(
            f"Seconds and Microseconds for {value} are not zeroed out.",
            code="validate_zeroed",
        )

    return True
