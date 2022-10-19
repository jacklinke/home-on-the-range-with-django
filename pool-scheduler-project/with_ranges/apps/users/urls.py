from django.urls import path

from .views import user_detail_view, user_list_view

app_name = "users"


urlpatterns = [
    path("<int:user_id>/", user_detail_view, name="user_detail_view"),
    path("", user_list_view, name="user_list_view"),
]
