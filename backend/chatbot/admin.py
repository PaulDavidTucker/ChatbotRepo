from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Client, ChatSession


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "domain",
        "api_key_short",
        "session_count",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "domain", "api_key"]
    readonly_fields = ["id", "api_key", "created_at", "updated_at", "created_by"]

    fieldsets = (
        (None, {"fields": ("name", "domain", "is_active")}),
        ("API Configuration", {"fields": ("api_key",)}),
        ("Configuration (JSON)", {"fields": ("config",)}),
        (
            "Metadata",
            {
                "fields": ("id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def api_key_short(self, obj):
        """Display shortened API key"""
        return f"{obj.api_key[:12]}..."

    api_key_short.short_description = "API Key"

    def session_count(self, obj):
        """Display total session count"""
        count = obj.sessions.count()
        color = "green" if count > 0 else "gray"
        return format_html('<span style="color: {};">{}</span>', color, count)

    session_count.short_description = "Sessions"

    def save_model(self, request, obj, form, change):
        """Set created_by to current user when creating"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id_short",
        "client_link",
        "session_id_short",
        "message_count",
        "started_at",
        "session_duration",
        "session_status",
    ]
    list_filter = ["started_at", "client"]
    search_fields = ["client__name", "client__domain", "session_id"]
    readonly_fields = ["id", "started_at", "ended_at"]
    raw_id_fields = ["client"]

    fieldsets = (
        (None, {"fields": ("client", "session_id")}),
        ("Session Data", {"fields": ("message_count", "started_at", "ended_at")}),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
    )

    def id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.id)[:8]

    id_short.short_description = "ID"

    def session_id_short(self, obj):
        """Display shortened session ID"""
        if len(obj.session_id) > 16:
            return f"{obj.session_id[:16]}..."
        return obj.session_id

    session_id_short.short_description = "Session ID"

    def client_link(self, obj):
        """Link to client admin page"""
        url = reverse("admin:chatbot_client_change", args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.name)

    client_link.short_description = "Client"

    def session_status(self, obj):
        """Display session status"""
        if obj.ended_at:
            return format_html('<span style="color: gray;">Ended</span>')
        return format_html('<span style="color: green;">Active</span>')

    session_status.short_description = "Status"

    def session_duration(self, obj):
        """Calculate and display session duration"""
        if obj.ended_at and obj.started_at:
            duration = obj.ended_at - obj.started_at
            seconds = int(duration.total_seconds())
            if seconds < 60:
                return f"{seconds}s"
            elif seconds < 3600:
                return f"{seconds // 60}m {seconds % 60}s"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                return f"{hours}h {minutes}m"
        return "—"

    session_duration.short_description = "Duration"
