from django.urls import path
from . import views

app_name = "myaccounts"

urlpatterns = [
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("profile/", views.UserChangeView.as_view(), name="profile"),
]
