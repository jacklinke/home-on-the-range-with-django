import logging

from apps.main.date_utils import get_this_month_range
from apps.main.models import (
    Closure,
    Lane,
    LaneReservation,
    Locker,
    LockerReservation,
    Pool,
)
from django.core.paginator import Paginator
from django.db.models import (
    Aggregate,
    CharField,
    DurationField,
    ExpressionWrapper,
    F,
    Func,
    Q,
    QuerySet,
    Value,
)
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils import timezone
from render_block import render_block_to_string

logger = logging.getLogger("with_ranges.main")


def home(request):
    """
    The primary home view
    """
    template = "main/home.html"
    context = {}
    return TemplateResponse(request, template, context)


def home_partial_view(request):
    """
    Content displayed on the home view and the pool/lane/locker tools home views
    """
    template = "main/home_content_partial.html"
    context = {}
    return TemplateResponse(request, template, context)


def pool_list_view(request):
    """
    Basic list of Pools within the municipality
    """
    template = "main/pool_list.html"
    context = {}
    context["pools"] = Pool.objects.all()
    return TemplateResponse(request, template, context)


def pool_tools_view(request):
    """
    The initial view for Pool Tools
    """
    template = "main/pool_tools.html"
    context = {}
    return TemplateResponse(request, template, context)


def pool_detail_view(request, pool_id):
    """
    Provides details about each Pool
    """
    template = "main/pool_detail.html"
    context = {}
    pool = get_object_or_404(Pool, id=pool_id)
    context["pool"] = pool
    return TemplateResponse(request, template, context)


def lane_tools_view(request):
    """
    The initial view for Lane Tools
    """
    template = "main/lane_tools.html"
    context = {}

    return TemplateResponse(request, template, context)


def locker_tools_view(request):
    """
    The initial view for Locker Tools
    """
    template = "main/locker_tools.html"
    context = {}
    return TemplateResponse(request, template, context)


def reservation_list_view(request):
    """
    Provides the initial paginated lists of Lane and Locker Reservations
    """
    template = "main/reservation_list.html"
    context = {}
    context["lane_reservations"] = LaneReservation.objects.all().order_by("period__startswith")[:20]
    context["locker_reservations"] = LockerReservation.objects.all().order_by("period__startswith")[:20]
    return TemplateResponse(request, template, context)
