from django.urls import path
from . import views

urlpatterns = [
    # Widget serving
    path("widget/v1/chatbot.js", views.serve_widget, name="serve_widget"),
    path("widget/demo/", views.widget_demo, name="widget_demo"),
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/analytics/", views.analytics, name="analytics"),
    path(
        "dashboard/client/<uuid:client_id>/", views.client_detail, name="client_detail"
    ),
    # API
    path("api/clients/", views.create_client, name="create_client"),
    path(
        "api/clients/<uuid:client_id>/config/",
        views.update_config,
        name="update_config",
    ),
]
