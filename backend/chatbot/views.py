import os
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render


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
