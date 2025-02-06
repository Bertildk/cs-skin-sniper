from django.urls import path

from csskinsnipe import views

urlpatterns = [
    path("", views.main, name="main"),
    path("scan", views.scan, name="scan"),
    path("refresh", views.refresh, name="refresh"),
    path("discord_notify", views.discord_notify, name="discord_notify"),
]
