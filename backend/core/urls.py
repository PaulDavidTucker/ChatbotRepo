from django.urls import path, include
from django.views.generic import TemplateView
from chatbot import admin,
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("chatbot.urls")),
]
