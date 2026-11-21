from django.urls import path

from . import views

urlpatterns = [
    path("message/", views.message, name="chat_message"),
    path("history/", views.history, name="chat_history"),
    path("clear/", views.clear, name="chat_clear"),
]
