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
from apps.main.forms import DateTimeRangeForm
from apps.main.models import Closure, Lane, LaneReservation, Pool
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


def get_lane_reservation_calendar_context(lane_reservation_queryset: QuerySet) -> dict:
    """
    Given a `LaneReservation` QuerySet, returns a context dictionary with the components needed
        to display reservations on a calendar, grouped by Lane

        This function allows us to inject a calendar into various views
    """
    lanes = (
        Lane.objects.filter(lane_reservations__in=lane_reservation_queryset)
        .order_by("id")
        .distinct("id")
        .values(
            "id",
            content=Concat(F("pool__name"), Value(" "), F("name"), output_field=CharField()),
        )
    )

    lane_reservation_queryset = lane_reservation_queryset.annotate(
        formatted_start=Func(
            F("period__startswith"), Value("YYYY-MM-DD HH24:MI:SS TZ"), function="to_char", output_field=CharField()
        ),
        formatted_end=Func(
            F("period__endswith"), Value("YYYY-MM-DD HH24:MI:SS TZ"), function="to_char", output_field=CharField()
        ),
    ).values(
        "id",
        content=Concat(
            Value("Lane id: "), F("lane__id"), Value(" , LaneReservation id: "), F("id"), output_field=CharField()
        ),
        group=F("lane__id"),
        start=F("formatted_start"),
        end=F("formatted_end"),
    )
    context = {}
    context["calendar_groups"] = list(lanes)
    context["calendar_reservations"] = list(lane_reservation_queryset)
    return context


def lane_reservation_partial_view(request):
    """
    This provides the paginated listing of lane reservations for `reservation_list_view()` in views.py
    """
    template = "main/lane_reservation_partials.html"
    context = {}
    lane_reservations = LaneReservation.objects.all().order_by("period__startswith")
    lane_paginator = Paginator(lane_reservations, 5)  # Show 5 lane_reservations per page

    lane_page_number = request.GET.get("page", 1)
    context["lane_reservations_page"] = lane_paginator.get_page(lane_page_number)

    html = render_block_to_string(template, "lane_reservation_list", context)
    return HttpResponse(html)


def lane_reservation_detail_view(request, lane_reservation_id):
    """
    List the details for a Lane Reservation
    """
    template = "main/lane_reservation_detail.html"
    context = {}
    lane_reservation = get_object_or_404(LaneReservation, id=lane_reservation_id)
    context["lane_reservation"] = lane_reservation
    return TemplateResponse(request, template, context)


def lane_reservation_actual_buttons_partial_view(request, lane_reservation_id):
    """
    Buttons to Check-in/Check-out/Cancel Lane Reservations. This view is injected via htmx into
        `lane_reservation_detail_view`
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservation = LaneReservation.objects.filter(id=lane_reservation_id).first()

    context["lane_reservation"] = lane_reservation
    html = render_block_to_string(template, "lane_reservation_actual_buttons", context)
    return HttpResponse(html)


def lane_reservation_cancel_partial_view(request, lane_reservation_id):
    """
    Handles cancellation of a Reservation
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservation = LaneReservation.objects.filter(id=lane_reservation_id).first()
    if lane_reservation is not None:
        lane_reservation.cancel_reservation()

    context["lane_reservation"] = lane_reservation
    html = render_block_to_string(template, "lane_reservation_cancelled", context)
    return HttpResponse(html)


def lane_reservation_check_in_partial_view(request, lane_reservation_id):
    """
    Handles check-in for a Reservation
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservation = LaneReservation.objects.filter(id=lane_reservation_id).first()
    if lane_reservation is not None:
        lane_reservation.check_in()

    context["lane_reservation"] = lane_reservation
    html = render_block_to_string(template, "lane_reservation_actual_buttons", context)
    return HttpResponse(html)


def lane_reservation_check_out_partial_view(request, lane_reservation_id):
    """
    Handles check-out for a Reservation
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservation = LaneReservation.objects.filter(id=lane_reservation_id).first()
    if lane_reservation is not None:
        lane_reservation.check_out()

    context["lane_reservation"] = lane_reservation
    html = render_block_to_string(template, "lane_reservation_actual_buttons", context)
    return HttpResponse(html)


def lane_reservations_greater_than_eight_hr_partial_view(request):
    """
    Provides a list and calendar of Reservations with an overall `period` duration of greater than 8 hours in length
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservations_greater_than_eight_hr = (
        LaneReservation.objects.all()
        .annotate(
            delta=ExpressionWrapper(
                F("period__endswith") - F("period__startswith"),
                output_field=DurationField(),
            )
        )
        .filter(delta__gt=timezone.timedelta(hours=8))
    )
    context["lane_reservations_greater_than_eight_hr"] = lane_reservations_greater_than_eight_hr

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_greater_than_eight_hr)}
    html = render_block_to_string(template, "lane_reservations_greater_than_eight_hr", context)
    return HttpResponse(html)


def lane_reservations_this_week_partial_view(request):
    """
    Provides a list and calendar of Reservations that overlap in any part with the current week, accounting for weeks
        that start on Sunday -or- Monday
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservations_this_week_starting_sunday = LaneReservation.objects.filter(
        period__overlap=get_this_week_range(starting_day_sunday=True)
    )
    context["lane_reservations_this_week_starting_sunday"] = lane_reservations_this_week_starting_sunday

    lane_reservations_this_week_starting_monday = LaneReservation.objects.filter(
        period__overlap=get_this_week_range(starting_day_sunday=False)
    )
    context["lane_reservations_this_week_starting_monday"] = lane_reservations_this_week_starting_monday

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_this_week_starting_sunday)}
    html = render_block_to_string(template, "lane_reservations_this_week", context)
    return HttpResponse(html)


def lane_reservations_this_month_partial_view(request):
    """
    Provides a list and calendar of Reservations that overlap in any part with the current month
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservations_this_month = LaneReservation.objects.filter(period__overlap=get_this_month_range())
    lane_paginator = Paginator(lane_reservations_this_month, 25)

    lane_page_number = request.GET.get("page")
    context["lane_reservations_this_month_page"] = lane_paginator.get_page(lane_page_number)

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_this_month)}
    html = render_block_to_string(template, "lane_reservations_this_month", context)
    return HttpResponse(html)


def lane_reservations_in_the_past_partial_view(request):
    """
    Provides a list and calendar of Reservations that occur in the past
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservations_in_the_past = LaneReservation.objects.filter(period__endswith__lt=timezone.now())
    context["lane_reservations_in_the_past"] = lane_reservations_in_the_past

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_in_the_past)}
    html = render_block_to_string(template, "lane_reservations_in_the_past", context)
    return HttpResponse(html)


def lane_reservations_year_to_date_partial_view(request):
    """
    Provides a list and calendar of Reservations that occurred between the beginning of this year (inclusive)
        to this moment (exclusive)
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservations_year_to_date = LaneReservation.objects.filter(
        period__overlap=DateTimeTZRange(get_start_datetime_of_this_year(), timezone.now())
    )
    context["lane_reservations_year_to_date"] = lane_reservations_year_to_date

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_year_to_date)}
    html = render_block_to_string(template, "lane_reservations_year_to_date", context)
    return HttpResponse(html)


def lane_reservations_til_end_of_year_partial_view(request):
    """
    Provides a list and calendar of Reservations that will occur from now until the first moment of next
        year (exclusive)
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservations_til_end_of_year = LaneReservation.objects.filter(
        period__overlap=DateTimeTZRange(timezone.now(), get_start_datetime_of_next_year())
    )
    context["lane_reservations_til_end_of_year"] = lane_reservations_til_end_of_year

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_til_end_of_year)}
    html = render_block_to_string(template, "lane_reservations_til_end_of_year", context)
    return HttpResponse(html)


def lane_reservations_overdue_start_partial_view(request):
    """
    Provides a list and calendar of Reservations that have a lower value of `period` which occurred in the past,
        but where the lower value of `actual` is `None`
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    now = timezone.now()

    lane_reservations_overdue_start = LaneReservation.objects.filter(
        period__startswith__lt=now, actual__startswith__isnull=True
    )
    context["lane_reservations_overdue_start"] = lane_reservations_overdue_start

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_overdue_start)}
    html = render_block_to_string(template, "lane_reservations_overdue_start", context)
    return HttpResponse(html)


def lane_reservations_overdue_end_partial_view(request):
    """
    Provides a list and calendar of Reservations that have a upper value of `period` which occurred in the past,
        but where the upper value of `actual` is `None`
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    now = timezone.now()

    lane_reservations_overdue_end = LaneReservation.objects.filter(
        period__endswith__lt=now, actual__endswith__isnull=True
    )
    context["lane_reservations_overdue_end"] = lane_reservations_overdue_end

    context = {**context, **get_lane_reservation_calendar_context(lane_reservations_overdue_end)}
    html = render_block_to_string(template, "lane_reservations_overdue_end", context)
    return HttpResponse(html)


def lane_reservations_average_length_of_all_partial_view(request):
    """
    Provides a simple view showing the average duration of all Reservations
    """
    template = "main/lane_reservation_partials.html"
    context = {}

    lane_reservations_average_length_of_all = LaneReservation.objects.annotate(
        time_elapsed=Sum(Cast(F("period__endswith") - F("period__startswith"), DurationField()))
    ).aggregate(time_elapsed_avg=Avg("time_elapsed"))

    average_time = lane_reservations_average_length_of_all["time_elapsed_avg"].seconds

    # Convert overall `timedelta` seconds into minutes, hours, and seconds
    hours, remainder = divmod(average_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    context["lane_reservations_average_length_of_all"] = f"{hours} hours, {minutes} minutes, {seconds} seconds"

    html = render_block_to_string(template, "lane_reservations_average_length_of_all", context)
    return HttpResponse(html)


def lane_reservations_contains_datetime_partial_view(request):
    """
    Demonstrates getting a date from a user using htmx and an input field, and then displaying the resulting
        filtered QuerySet data

    - GET request will return a template containing the range search input box and an empty #outputDiv
    - POST request will return just the #outputDiv contents, limited to the results filtered by the range search
        input box value
    """

    template = "main/lane_reservation_partials.html"
    context = {}

    if request.method == "POST":
        raw_string_list = request.POST.get("datetime_input", "")
        # ToDo: Input validation is important, but skipped here to keep concise
        datetime_input = get_datetime_from_string(raw_string_list)

        lane_reservations_filtered = LaneReservation.objects.filter(period__contains=datetime_input)

        context["lane_reservations_filtered"] = lane_reservations_filtered

        context = {**context, **get_lane_reservation_calendar_context(lane_reservations_filtered)}
        html = render_block_to_string(template, "lane_reservations_contains_datetime_inner_content", context)
        return HttpResponse(html)

    html = render_block_to_string(template, "lane_reservations_contains_datetime", context)
    return HttpResponse(html)


def lane_reservations_overlapping_datetime_form_partial_view(request):
    """
    Demonstrates getting range data from a user using Django Forms, and then displaying the resulting filtered
        QuerySet data

    - GET request will return a template containing the form (with the range search input box) and an empty #outputDiv
    - POST request will return just the #outputDiv contents, limited to the results filtered by the range search
        input box value
    """

    template = "main/lane_reservation_partials.html"
    context = {}

    form = DateTimeRangeForm(request.POST or None)

    # We dynamically add the url which htmx will use to post the form, keeping the form generic enough to use with both
    #   Lanes and Lockers
    form.fields["datetimerange_input"].widget.attrs["hx-post"] = reverse_lazy(
        "main:lane_reservations_overlapping_datetime_form"
    )
    context["form"] = form

    if request.method == "POST":
        if form.is_valid():
            input_range = form.cleaned_data["datetimerange_input"]
            lane_reservations_filtered = LaneReservation.objects.filter(period__overlap=input_range)

            context["lane_reservations_filtered"] = lane_reservations_filtered

            context = {**context, **get_lane_reservation_calendar_context(lane_reservations_filtered)}
            html = render_block_to_string(template, "lane_reservations_overlapping_datetime_inner_content", context)
            return HttpResponse(html)

    html = render_block_to_string(template, "lane_reservations_overlapping_datetime_form", context)
    return HttpResponse(html)


def lane_reservations_overlapping_datetime_manual_partial_view(request):
    """
    Demonstrates getting range data from a user using htmx and an input field, and then displaying the resulting
        filtered QuerySet data

    - GET request will return a template containing the range search input box and an empty #outputDiv
    - POST request will return just the #outputDiv contents, limited to the results filtered by the range search
        input box value
    """

    template = "main/lane_reservation_partials.html"
    context = {}

    if request.method == "POST":
        raw_string_list = request.POST.get("datetimerange_input", "").split(" - ", 1)
        # ToDo: Input validation is important, but skipped here to keep concise
        input_range = get_datetime_range_from_string_list(raw_string_list)

        lane_reservations_filtered = LaneReservation.objects.filter(period__overlap=input_range)

        context["lane_reservations_filtered"] = lane_reservations_filtered

        context = {**context, **get_lane_reservation_calendar_context(lane_reservations_filtered)}
        html = render_block_to_string(template, "lane_reservations_overlapping_datetime_inner_content", context)
        return HttpResponse(html)

    html = render_block_to_string(template, "lane_reservations_overlapping_datetime_manual", context)
    return HttpResponse(html)
