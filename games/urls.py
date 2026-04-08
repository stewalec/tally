from django.urls import path
from . import views

urlpatterns = [
    path("", views.leaderboard, name="leaderboard"),
    path("users/<slug:username>/", views.user_detail, name="user_detail"),
]
