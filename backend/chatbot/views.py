from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Client, ChatbotConfiguration, ChatSession, ChatMessage
import json


@staff_member_required
def dashboard(request):
    """Enhanced dashboard with analytics"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Basic stats
    total_clients = Client.objects.filter(is_active=True).count()
    total_sessions_today = ChatSession.objects.filter(started_at__date=today).count()
    total_messages_today = ChatMessage.objects.filter(created_at__date=today).count()

    # Usage over time (last 7 days)
    usage_data = []
    labels = []
    for i in range(7):
        date = today - timedelta(days=6 - i)
        count = ChatMessage.objects.filter(created_at__date=date).count()
        usage_data.append(count)
        labels.append(date.strftime("%m/%d"))

    # Top domains
    domain_stats = (
        ChatSession.objects.values("domain")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Enhanced client data
    clients = []
    for client in Client.objects.all().order_by("-created_at"):
        last_session = (
            ChatSession.objects.filter(client=client).order_by("-started_at").first()
        )
        total_sessions = ChatSession.objects.filter(client=client).count()
        total_messages = ChatMessage.objects.filter(session__client=client).count()
        avg_response_time = (
            ChatMessage.objects.filter(session__client=client).aggregate(
                avg_time=Avg("response_time_ms")
            )["avg_time"]
            or 0
        )

        clients.append(
            {
                **client.__dict__,
                "last_activity": last_session.started_at if last_session else None,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "avg_response_time": int(avg_response_time),
                "usage_percentage": (
                    client.current_month_usage / client.monthly_message_limit
                )
                * 100
                if client.monthly_message_limit > 0
                else 0,
            }
        )

    context = {
        "clients": clients,
        "total_clients": total_clients,
        "total_sessions_today": total_sessions_today,
        "total_messages_today": total_messages_today,
        "estimated_revenue": total_clients * 100,  # Simple estimation
        "usage_chart_data": json.dumps({"labels": labels, "data": usage_data}),
        "domains_chart_data": json.dumps(
            {
                "labels": [stat["domain"] for stat in domain_stats],
                "data": [stat["count"] for stat in domain_stats],
            }
        ),
    }

    return render(request, "dashboard/dashboard.html", context)


@staff_member_required
def client_detail(request, client_id):
    """Enhanced client detail view"""
    client = get_object_or_404(Client, id=client_id)
    sessions = ChatSession.objects.filter(client=client).order_by("-started_at")[:50]

    # Calculate additional stats
    total_sessions = ChatSession.objects.filter(client=client).count()
    total_messages = ChatMessage.objects.filter(session__client=client).count()
    avg_response_time = (
        ChatMessage.objects.filter(session__client=client).aggregate(
            avg_time=Avg("response_time_ms")
        )["avg_time"]
        or 0
    )

    # Add duration to sessions
    for session in sessions:
        if session.ended_at:
            duration = session.ended_at - session.started_at
            session.duration = f"{duration.total_seconds():.0f}s"

    context = {
        "client": client,
        "sessions": sessions,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "avg_response_time": int(avg_response_time),
    }

    return render(request, "client_detail.html", context)


def serve_widget(request):
    """Serve the compiled widget JavaScript"""
    # For now, serve a simple widget loader
    widget_content = """
(function() {
    window.initChatbot = function(config) {
        // Create widget container
        const container = document.createElement('div');
        container.id = 'chatbot-widget-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(container);

        // Create widget button
        const button = document.createElement('div');
        button.style.cssText = `
            width: 60px;
            height: 60px;
            background: ${config.primaryColor || '#007bff'};
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: transform 0.2s;
        `;
        button.innerHTML = '💬';
        button.onclick = toggleChat;
        container.appendChild(button);

        // Create chat window
        const chatWindow = document.createElement('div');
        chatWindow.id = 'chatbot-window';
        chatWindow.style.cssText = `
            position: absolute;
            bottom: 70px;
            right: 0;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            display: none;
            flex-direction: column;
        `;

        chatWindow.innerHTML = `
            <div style="padding: 15px; background: ${config.primaryColor || '#007bff'}; color: white; border-radius: 10px 10px 0 0;">
                <h4 style="margin: 0; font-size: 16px;">${config.title || 'AI Assistant'}</h4>
            </div>
            <div id="chat-messages" style="flex: 1; padding: 15px; overflow-y: auto;">
                <div style="background: #f1f3f5; padding: 10px; border-radius: 15px; margin-bottom: 10px;">
                    ${config.welcomeMessage || 'Hello! How can I help you?'}
                </div>
            </div>
            <div style="padding: 15px; border-top: 1px solid #eee;">
                <div style="display: flex; gap: 10px;">
                    <input type="text" id="chat-input" placeholder="Type a message..."
                           style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none;">
                    <button id="chat-send" style="padding: 10px 15px; background: ${config.primaryColor || '#007bff'};
                            color: white; border: none; border-radius: 50%; cursor: pointer;">→</button>
                </div>
            </div>
        `;

        container.appendChild(chatWindow);

        // Initialize WebSocket
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${wsProtocol}${config.apiEndpoint}/ws/chat/${config.apiKey}/?domain=${encodeURIComponent(window.location.hostname)}`;
        const socket = new WebSocket(wsUrl);

        const messagesContainer = chatWindow.querySelector('#chat-messages');
        const input = chatWindow.querySelector('#chat-input');
        const sendButton = chatWindow.querySelector('#chat-send');

        function addMessage(message, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.style.cssText = `
                padding: 10px;
                margin: 5px 0;
                border-radius: 15px;
                max-width: 80%;
                ${sender === 'user' ?
                    `background: ${config.primaryColor || '#007bff'}; color: white; margin-left: auto;` :
                    'background: #f1f3f5; margin-right: auto;'
                }
            `;
            messageDiv.textContent = message;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function sendMessage() {
            const message = input.value.trim();
            if (message && socket.readyState === WebSocket.OPEN) {
                addMessage(message, 'user');
                socket.send(JSON.stringify({ message }));
                input.value = '';
            }
        }

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.message) {
                addMessage(data.message, 'bot');
            }
        };

        sendButton.onclick = sendMessage;
        input.onkeypress = (e) => {
            if (e.key === 'Enter') sendMessage();
        };

        function toggleChat() {
            const isVisible = chatWindow.style.display === 'flex';
            chatWindow.style.display = isVisible ? 'none' : 'flex';
            if (!isVisible) input.focus();
        }
    };
})();
"""

    return HttpResponse(widget_content, content_type="application/javascript")
