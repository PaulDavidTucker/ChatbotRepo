import os
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from .models import Client, ChatSession


def serve_widget(request):
    """Serve the compiled widget JavaScript"""
    widget_path = os.path.join(
        settings.BASE_DIR, "static", "chatbot", "js", "chatbot-widget.js"
    )

    try:
        with open(widget_path, "r") as f:
            widget_content = f.read()
    except FileNotFoundError:
        # Fallback to basic widget if built version doesn't exist
        widget_content = """
console.error('Widget not built yet. Run npm run build-widget first.');
window.initChatbot = function(config) {
    console.log('Chatbot config:', config);
    alert('Widget not built yet. Please run the build script.');
};
"""

    response = HttpResponse(widget_content, content_type="application/javascript")
    response["Access-Control-Allow-Origin"] = "*"
    return response


def widget_demo(request):
    """Demo page for testing the widget"""
    return render(request, "widget/demo.html")


# Add analytics view
@staff_member_required
def analytics(request):
    """Analytics dashboard"""
    # Add your analytics logic here
    context = {
        "total_sessions": 150,
        "total_messages": 1250,
        "avg_session_length": 180,
        "avg_response_time": 450,
        "tool_usage": 45,
        "unique_domains": 12,
        # Add more analytics data
    }
    return render(request, "dashboard/analytics.html", context)


@staff_member_required
def dashboard(request):
    """Main Dashboard"""
    # Get all active clients with session counts
    clients = Client.objects.filter(is_active=True).annotate(
        session_count=Count("sessions"), total_messages=Sum("sessions__message_count")
    )

    # Get recent sessions across all clients
    recent_sessions = ChatSession.objects.select_related("client").order_by(
        "-started_at"
    )[:10]

    # Overall stats
    context = {
        "clients": clients,
        "recent_sessions": recent_sessions,
        "total_clients": clients.count(),
        "total_sessions": ChatSession.objects.count(),
    }

    return render(request, "dashboard/dashboard.html", context)


@staff_member_required
def client_detail(request, client_id):
    """Detailed view for a specific client"""
    client = get_object_or_404(Client, id=client_id)

    # Get sessions for this client
    sessions = client.sessions.all()[:50]  # Last 50 sessions

    # Calculate statistics
    last_30_days = timezone.now() - timedelta(days=30)
    recent_sessions = client.sessions.filter(started_at__gte=last_30_days)

    stats = {
        "total_sessions": client.sessions.count(),
        "sessions_last_30_days": recent_sessions.count(),
        "total_messages": client.sessions.aggregate(total=Sum("message_count"))["total"]
        or 0,
        "avg_messages_per_session": client.sessions.aggregate(avg=Avg("message_count"))[
            "avg"
        ]
        or 0,
    }

    context = {
        "client": client,
        "sessions": sessions,
        "stats": stats,
    }

    return render(request, "dashboard/client_detail.html", context)


# API Views
@staff_member_required
@require_http_methods(["POST"])
def create_client(request):
    """
    API endpoint to create a new client.

    Expected JSON payload:
    {
        "name": "Client Name",
        "domain": "example.com",
        "config": {
            "theme": "light",
            "position": "bottom-right",
            ...
        }
    }
    """
    try:
        data = json.loads(request.body)

        # Validate required fields
        if not data.get("name") or not data.get("domain"):
            return JsonResponse({"error": "name and domain are required"}, status=400)

        # Check if domain already exists
        if Client.objects.filter(domain=data["domain"]).exists():
            return JsonResponse({"error": "Domain already registered"}, status=409)

        # Create client
        client = Client.objects.create(
            name=data["name"],
            domain=data["domain"],
            config=data.get("config", {}),
            created_by=request.user,
        )

        return JsonResponse(
            {
                "id": str(client.id),
                "name": client.name,
                "domain": client.domain,
                "api_key": client.api_key,
                "config": client.config,
                "created_at": client.created_at.isoformat(),
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)


@csrf_exempt  # You may want to use proper API authentication instead
@require_http_methods(["PUT", "PATCH"])
def update_config(request, client_id):
    """
    API endpoint to update client configuration.

    Expected JSON payload:
    {
        "theme": "dark",
        "position": "bottom-left",
        "primaryColor": "#007bff",
        ...
    }

    Supports both PUT (full replace) and PATCH (partial update)
    """
    try:
        client = get_object_or_404(Client, id=client_id)

        # Verify API key from header
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != client.api_key:
            return JsonResponse({"error": "Invalid API key"}, status=403)

        data = json.loads(request.body)

        if request.method == "PUT":
            # Full config replacement
            client.config = data
        else:  # PATCH
            # Partial update - merge with existing config
            client.config.update(data)

        client.save()

        return JsonResponse(
            {
                "id": str(client.id),
                "config": client.config,
                "updated_at": client.updated_at.isoformat(),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)
