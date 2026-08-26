from django.urls import path

from apps.trends.views import RadarView

urlpatterns = [
    path("radar/", RadarView.as_view(), name="radar"),
]
