from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="profile"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
]
