import logging

from apps.users.models import User
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

logger = logging.getLogger("with_ranges.users")

# Create your views here.


def user_list_view(request):
    template = "users/user_list.html"
    context = {}
    context["users"] = User.objects.all().order_by("email")
    return TemplateResponse(request, template, context)


def user_detail_view(request, user_id):
    template = "users/user_detail.html"
    context = {}
    user = get_object_or_404(User, id=user_id)
    context["user"] = user
    context["lane_reservations_count"] = user.lane_reservations.count()
    context["locker_reservations_count"] = user.locker_reservations.count()
    return TemplateResponse(request, template, context)
