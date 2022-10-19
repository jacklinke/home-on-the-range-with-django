from dateutil.relativedelta import relativedelta
from django.utils import timezone
from psycopg2.extras import DateRange, DateTimeTZRange


def get_start_datetime_of_this_year():
    return timezone.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def get_start_datetime_of_next_year():
    this_year = timezone.datetime.now().date().year
    return timezone.datetime.now().replace(
        year=this_year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )


def get_this_month_range() -> DateTimeTZRange:
    """
    Return a DateTimeTZRange range covering the entirety of current month
    """
    today = timezone.now().date()
    if today.day > 25:
        today += timezone.timedelta(7)
    this_month_start = today.replace(day=1)
    next_month_start = this_month_start + relativedelta(months=1)
    return DateTimeTZRange(this_month_start, next_month_start)


def get_this_week_range(starting_day_sunday: bool = True) -> DateTimeTZRange:
    """
    Return a DateTimeTZRange range covering the entirety of current week, starting on either Sunday or Monday
    """
    today = timezone.now().date()

    if starting_day_sunday:
        # This section starts the week on Sunday to Saturday
        start_date = today - timezone.timedelta(days=(today.weekday() + 1) % 7)
        end_date = start_date + timezone.timedelta(days=6)

    else:
        # This section starts the week on Monday to Sunday
        start_date = today - timezone.timedelta(days=today.weekday())
        end_date = start_date + timezone.timedelta(days=6)

    return DateTimeTZRange(start_date, end_date)


def get_date_from_string(date_string: str) -> timezone.datetime.date:
    """Converts a string in the format "MM/DD/YYYY" to a date object"""
    # We convert a string to actual Python datetime object
    # %m = Month as a zero-padded decimal number
    # %d = Day as a zero-padded decimal number
    # %Y = 4-digit year
    return timezone.datetime.strptime(date_string, "%m/%d/%Y").date()


def get_datetime_from_string(datetime_string: str) -> timezone.datetime:
    """Converts a string in the format "MM/DD/YYYY (HH:MM)" to a datetime object"""
    # We convert a string to actual Python datetime object
    # %m = Month as a zero-padded decimal number
    # %d = Day as a zero-padded decimal number
    # %Y = 4-digit year
    # %H = 2-digit hour in zero-padded 24-hour format
    # %M = Minute as a zero-padded decimal number
    return timezone.datetime.strptime(datetime_string, "%m/%d/%Y (%H:%M)")


def get_date_range_from_string_list(date_string_list: list = list) -> DateRange:
    """
    Given a list of two strings containing date values in the form "MM/DD/YYYY", converts these to Django
        date values, and returns them in a DateRange as the lower and upper range values.

    If the strings are not properly formatted, raises a ValueError, which we can catch in the form field's clean
        method, and return as a field ValidationError.
    """
    lower = get_date_from_string(date_string_list[0])
    upper = get_date_from_string(date_string_list[1])
    return DateRange(lower, upper)


def get_datetime_range_from_string_list(datetime_string_list: list = list) -> DateTimeTZRange:
    """
    Given a list of two strings containing datetime values in the form "MM/DD/YYYY (HH:MM)", converts these to Django
        timezone datetime values, and returns them in a DateTimeTZRange as the lower and upper range values.

    If the strings are not properly formatted, raises a ValueError, which we can catch in the form field's clean
        method, and return as a field ValidationError.
    """
    lower = get_datetime_from_string(datetime_string_list[0])
    upper = get_datetime_from_string(datetime_string_list[1])
    return DateTimeTZRange(lower, upper)
