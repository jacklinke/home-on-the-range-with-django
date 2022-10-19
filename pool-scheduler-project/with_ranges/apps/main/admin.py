import logging

from apps.main.models import (
    Closure,
    Lane,
    LaneReservation,
    Locker,
    LockerReservation,
    Pool,
)
from django.contrib import admin
from django.db.models import Count, F

logger = logging.getLogger("apps.main")


@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    pass


@admin.register(Locker)
class LockerAdmin(admin.ModelAdmin):
    pass


@admin.register(LockerReservation)
class LockerReservationAdmin(admin.ModelAdmin):
    pass


@admin.register(LaneReservation)
class LaneReservationAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "user_count",
        "max_swimmers_allowed",
        "additional_swimmers_allowed",
    ]

    def user_count(self, obj):
        return obj.user_count

    def max_swimmers_allowed(self, obj):
        return obj.max_swimmers_allowed

    def additional_swimmers_allowed(self, obj):
        return obj.max_swimmers_allowed - obj.user_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(user_count=Count("users")).annotate(max_swimmers_allowed=F("lane__max_swimmers"))
        return queryset


@admin.register(Closure)
class ClosureAdmin(admin.ModelAdmin):
    pass


@admin.register(Lane)
class LaneAdmin(admin.ModelAdmin):
    pass
