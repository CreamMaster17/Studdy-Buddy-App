from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "accounts"

urlpatterns = [
    path("home/", views.home, name="home"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("login/", views.login_page, name="login"),
    path("registration/", views.registration_page, name="registration"),
    path("Test_Insert/", views.test_insert, name="Test_Insert"),
]