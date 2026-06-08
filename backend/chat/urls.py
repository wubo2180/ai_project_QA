from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.chat_message, name="chat"),
    path("health/", views.health_check, name="health"),
]
