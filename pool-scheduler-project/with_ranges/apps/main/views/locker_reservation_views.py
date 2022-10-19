import logging

from apps.main.date_utils import (
    get_date_from_string,
    get_date_range_from_string_list,
    get_datetime_from_string,
    get_datetime_range_from_string_list,
    get_start_datetime_of_next_year,
    get_start_datetime_of_this_year,
    get_this_month_range,
    get_this_week_range,
)
from apps.main.forms import DateTimeRangeFieldForm, DateTimeRangeForm
from apps.main.models import Closure, Locker, LockerReservation, Pool
from django.core.paginator import Paginator
from django.db.models import (
    Aggregate,
    Avg,
    CharField,
    DurationField,
    ExpressionWrapper,
    F,
    Func,
    Q,
    QuerySet,
    Sum,
    Value,
)
from django.db.models.functions import Cast, Concat
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange
from render_block import render_block_to_string

logger = logging.getLogger("with_ranges.main")


def get_locker_reservation_calendar_context(locker_reservation_queryset: QuerySet) -> dict:
    """
    Given a `LockerReservation` QuerySet, returns a context dictionary with the components needed
        to display reservations on a calendar, grouped by Locker

        This function allows us to inject a calendar into various views
    """
    lockers = (
        Locker.objects.filter(locker_reservations__in=locker_reservation_queryset)
        .order_by("id")
        .distinct("id")
        .values(
            "id",
            content=Concat(F("pool__name"), Value(" "), F("number"), output_field=CharField()),
        )
    )

    locker_reservation_queryset = locker_reservation_queryset.annotate(
        formatted_start=Func(
            F("period__startswith"), Value("YYYY-MM-DD HH24:MI:SS TZ"), function="to_char", output_field=CharField()
        ),
        formatted_end=Func(
            F("period__endswith"), Value("YYYY-MM-DD HH24:MI:SS TZ"), function="to_char", output_field=CharField()
        ),
    ).values(
        "id",
        content=Concat(
            Value("Locker id: "), F("locker__id"), Value(" , LockerReservation id: "), F("id"), output_field=CharField()
        ),
        group=F("locker__id"),
        start=F("formatted_start"),
        end=F("formatted_end"),
    )
    context = {}
    context["calendar_groups"] = list(lockers)
    context["calendar_reservations"] = list(locker_reservation_queryset)
    return context


def locker_reservation_partial_view(request):
    """
    This provides the paginated listing of lane reservations for `reservation_list_view()` in views.py
    """
    template = "main/locker_reservation_partials.html"
    context = {}
    locker_reservations = LockerReservation.objects.all().order_by("period__startswith")
    locker_paginator = Paginator(locker_reservations, 5)  # Show 5 locker_reservations per page

    locker_page_number = request.GET.get("page", 1)
    context["locker_reservations_page"] = locker_paginator.get_page(locker_page_number)

    html = render_block_to_string(template, "locker_reservation_list", context)
    return HttpResponse(html)


def locker_reservation_detail_view(request, locker_reservation_id):
    """
    List the details for a Locker Reservation
    """
    template = "main/locker_reservation_detail.html"
    context = {}
    locker_reservation = get_object_or_404(LockerReservation, id=locker_reservation_id)
    context["locker_reservation"] = locker_reservation
    return TemplateResponse(request, template, context)


def locker_reservation_actual_buttons_partial_view(request, locker_reservation_id):
    """
    Buttons to Check-in/Check-out/Cancel Locker Reservations. This view is injected via htmx into
        `lane_reservation_detail_view`
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservation = LockerReservation.objects.filter(id=locker_reservation_id).first()

    context["locker_reservation"] = locker_reservation
    html = render_block_to_string(template, "locker_reservation_actual_buttons", context)
    return HttpResponse(html)


def locker_reservation_cancel_partial_view(request, locker_reservation_id):
    """
    Handles cancellation of a Reservation
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservation = LockerReservation.objects.filter(id=locker_reservation_id).first()
    if locker_reservation is not None:
        locker_reservation.cancel_reservation()

    context["locker_reservation"] = locker_reservation
    html = render_block_to_string(template, "locker_reservation_cancelled", context)
    return HttpResponse(html)


def locker_reservation_check_in_partial_view(request, locker_reservation_id):
    """
    Handles check-in for a Reservation
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservation = LockerReservation.objects.filter(id=locker_reservation_id).first()
    if locker_reservation is not None:
        locker_reservation.check_in()

    context["locker_reservation"] = locker_reservation
    html = render_block_to_string(template, "locker_reservation_actual_buttons", context)
    return HttpResponse(html)


def locker_reservation_check_out_partial_view(request, locker_reservation_id):
    """
    Handles check-out for a Reservation
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservation = LockerReservation.objects.filter(id=locker_reservation_id).first()
    if locker_reservation is not None:
        locker_reservation.check_out()

    context["locker_reservation"] = locker_reservation
    html = render_block_to_string(template, "locker_reservation_actual_buttons", context)
    return HttpResponse(html)


def locker_reservations_greater_than_thirty_days_partial_view(request):
    """
    Provides a list and calendar of Reservations with an overall `period` duration of greater than 30 days in length
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservations_greater_than_thirty_days = (
        LockerReservation.objects.all()
        .annotate(
            delta=ExpressionWrapper(
                F("period__endswith") - F("period__startswith"),
                output_field=DurationField(),
            )
        )
        .filter(delta__gt=timezone.timedelta(days=30))
    )
    context["locker_reservations_greater_than_thirty_days"] = locker_reservations_greater_than_thirty_days

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_greater_than_thirty_days)}
    html = render_block_to_string(template, "locker_reservations_greater_than_thirty_days", context)
    return HttpResponse(html)


def locker_reservations_this_month_partial_view(request):
    """
    Provides a list and calendar of Reservations that overlap in any part with the current month
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservations_this_month = LockerReservation.objects.filter(period__overlap=get_this_month_range())
    locker_paginator = Paginator(locker_reservations_this_month, 25)

    locker_page_number = request.GET.get("page")
    context["locker_reservations_this_month_page"] = locker_paginator.get_page(locker_page_number)

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_this_month)}
    html = render_block_to_string(template, "locker_reservations_this_month", context)
    return HttpResponse(html)


def locker_reservations_in_the_past_partial_view(request):
    """
    Provides a list and calendar of Reservations that occur in the past
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservations_in_the_past = LockerReservation.objects.filter(period__endswith__lt=timezone.now())
    context["locker_reservations_in_the_past"] = locker_reservations_in_the_past

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_in_the_past)}
    html = render_block_to_string(template, "locker_reservations_in_the_past", context)
    return HttpResponse(html)


def locker_reservations_year_to_date_partial_view(request):
    """
    Provides a list and calendar of Reservations that occurred between the beginning of this year (inclusive)
        to this moment (exclusive)
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservations_year_to_date = LockerReservation.objects.filter(
        period__overlap=DateTimeTZRange(get_start_datetime_of_this_year(), timezone.now())
    )
    context["locker_reservations_year_to_date"] = locker_reservations_year_to_date

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_year_to_date)}
    html = render_block_to_string(template, "locker_reservations_year_to_date", context)
    return HttpResponse(html)


def locker_reservations_til_end_of_year_partial_view(request):
    """
    Provides a list and calendar of Reservations that will occur from now until the first moment of next
        year (exclusive)
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservations_til_end_of_year = LockerReservation.objects.filter(
        period__overlap=DateTimeTZRange(timezone.now(), get_start_datetime_of_next_year())
    )
    context["locker_reservations_til_end_of_year"] = locker_reservations_til_end_of_year

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_til_end_of_year)}
    html = render_block_to_string(template, "locker_reservations_til_end_of_year", context)
    return HttpResponse(html)


def locker_reservations_oct_or_dec_this_year_partial_view(request):
    """
    Provides a list and calendar of Reservations that have an upper value of `period` where the year matches the
        current year, and month number is 10 (October) or 12 (December)
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservations_oct_or_dec_this_year = LockerReservation.objects.filter(
        period__endswith__month__in=[10, 12], period__endswith__year=timezone.now().year
    )

    context["locker_reservations_oct_or_dec_this_year"] = locker_reservations_oct_or_dec_this_year

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_oct_or_dec_this_year)}
    html = render_block_to_string(template, "locker_reservations_oct_or_dec_this_year", context)
    return HttpResponse(html)


def locker_reservations_overdue_start_partial_view(request):
    """
    Provides a list and calendar of Reservations that have a lower value of `period` which occurred in the past,
        but where the lower value of `actual` is `None`
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    now = timezone.now()

    locker_reservations_overdue_start = LockerReservation.objects.filter(
        period__startswith__lt=now, actual__startswith__isnull=True
    )
    context["locker_reservations_overdue_start"] = locker_reservations_overdue_start

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_overdue_start)}
    html = render_block_to_string(template, "locker_reservations_overdue_start", context)
    return HttpResponse(html)


def locker_reservations_overdue_end_partial_view(request):
    """
    Provides a list and calendar of Reservations that have a upper value of `period` which occurred in the past,
        but where the upper value of `actual` is `None`
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    now = timezone.now()

    locker_reservations_overdue_end = LockerReservation.objects.filter(
        period__endswith__lt=now, actual__endswith__isnull=True
    )
    context["locker_reservations_overdue_end"] = locker_reservations_overdue_end

    context = {**context, **get_locker_reservation_calendar_context(locker_reservations_overdue_end)}
    html = render_block_to_string(template, "locker_reservations_overdue_end", context)
    return HttpResponse(html)


def locker_reservations_average_length_of_all_partial_view(request):
    """
    Provides a simple view showing the average duration of all Reservations
    """
    template = "main/locker_reservation_partials.html"
    context = {}

    locker_reservations_average_length_of_all = LockerReservation.objects.annotate(
        time_elapsed=Sum(Cast(F("period__endswith") - F("period__startswith"), DurationField()))
    ).aggregate(time_elapsed_avg=Avg("time_elapsed"))

    context["locker_reservations_average_length_of_all"] = str(
        locker_reservations_average_length_of_all["time_elapsed_avg"]
    )

    html = render_block_to_string(template, "locker_reservations_average_length_of_all", context)
    return HttpResponse(html)


def locker_reservations_contains_date_partial_view(request):
    """
    Demonstrates getting a date from a user using htmx and an input field, and then displaying the resulting
        filtered QuerySet data

    - GET request will return a template containing the range search input box and an empty #outputDiv
    - POST request will return just the #outputDiv contents, limited to the results filtered by the range search
        input box value
    """

    template = "main/locker_reservation_partials.html"
    context = {}

    if request.method == "POST":
        raw_string_list = request.POST.get("date_input", "")
        # ToDo: Input validation is important, but skipped here to keep concise
        date_input = get_date_from_string(raw_string_list)

        locker_reservations_filtered = LockerReservation.objects.filter(period__contains=date_input)

        context["locker_reservations_filtered"] = locker_reservations_filtered

        context = {**context, **get_locker_reservation_calendar_context(locker_reservations_filtered)}
        html = render_block_to_string(template, "locker_reservations_contains_date_inner_content", context)
        return HttpResponse(html)

    html = render_block_to_string(template, "locker_reservations_contains_date", context)
    return HttpResponse(html)


def locker_reservations_overlapping_datetime_form_partial_view(request):
    """
    Demonstrates getting range data from a user using Django Forms, and then displaying the resulting filtered
        QuerySet data

    - GET request will return a template containing the form (with the range search input box) and an empty #outputDiv
    - POST request will return just the #outputDiv contents, limited to the results filtered by the range search
        input box value
    """

    template = "main/locker_reservation_partials.html"
    context = {}

    form = DateTimeRangeForm(request.POST or None)

    # We dynamically add the url which htmx will use to post the form, keeping the form generic enough to use with both
    #   Lanes and Lockers
    form.fields["datetimerange_input"].widget.attrs["hx-post"] = reverse_lazy(
        "main:locker_reservations_overlapping_datetime_form"
    )
    context["form"] = form

    if request.method == "POST":
        if form.is_valid():
            input_range = form.cleaned_data["datetimerange_input"]
            locker_reservations_filtered = LockerReservation.objects.filter(period__overlap=input_range)

            context["locker_reservations_filtered"] = locker_reservations_filtered

            context = {**context, **get_locker_reservation_calendar_context(locker_reservations_filtered)}
            html = render_block_to_string(template, "locker_reservations_overlapping_datetime_inner_content", context)
            return HttpResponse(html)

    html = render_block_to_string(template, "locker_reservations_overlapping_datetime_form", context)
    return HttpResponse(html)


def locker_reservations_overlapping_datetime_rangefield_form_partial_view(request):
    """
    Demonstrates getting range data from a user using Django Forms, and then displaying the resulting filtered
        QuerySet data

    - GET request will return a template containing the form (with the range search input box) and an empty #outputDiv
    - POST request will return just the #outputDiv contents, limited to the results filtered by the range search
        input box value
    """

    template = "main/locker_reservation_partials.html"
    context = {}

    form = DateTimeRangeFieldForm(request.POST or None)
    context["form"] = form

    if request.method == "POST":
        if form.is_valid():
            input_range = form.cleaned_data["datetimerange_input"]
            print(f"input_range: {input_range}")

            locker_reservations_filtered = LockerReservation.objects.filter(period__overlap=input_range)

            context["locker_reservations_filtered"] = locker_reservations_filtered

            context = {**context, **get_locker_reservation_calendar_context(locker_reservations_filtered)}
            html = render_block_to_string(template, "locker_reservations_overlapping_datetime_inner_content", context)
            return HttpResponse(html)

    html = render_block_to_string(template, "locker_reservations_overlapping_datetime_rangefield_form", context)
    return HttpResponse(html)


def locker_reservations_overlapping_datetime_manual_partial_view(request):
    """
    Demonstrates getting range data from a user using htmx and an input field, and then displaying the resulting
        filtered QuerySet data

    - GET request will return a template containing the range search input box and an empty #outputDiv
    - POST request will return just the #outputDiv contents, limited to the results filtered by the range search
        input box value
    """

    template = "main/locker_reservation_partials.html"
    context = {}

    if request.method == "POST":
        raw_string_list = request.POST.get("datetimerange_input", "").split(" - ", 1)
        # ToDo: Input validation is important, but skipped here to keep concise
        input_range = get_datetime_range_from_string_list(raw_string_list)

        locker_reservations_filtered = LockerReservation.objects.filter(period__overlap=input_range)

        context["locker_reservations_filtered"] = locker_reservations_filtered

        context = {**context, **get_locker_reservation_calendar_context(locker_reservations_filtered)}
        html = render_block_to_string(template, "locker_reservations_overlapping_datetime_inner_content", context)
        return HttpResponse(html)

    html = render_block_to_string(template, "locker_reservations_overlapping_datetime_manual", context)
    return HttpResponse(html)
