from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Client, ChatbotConfiguration, ChatSession, ChatMessage


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "api_key_short",
        "usage_display",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "email", "api_key")
    readonly_fields = ("id", "api_key", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "email", "is_active")}),
        ("API Configuration", {"fields": ("api_key", "allowed_domains")}),
        ("Usage Limits", {"fields": ("monthly_message_limit", "current_month_usage")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def api_key_short(self, obj):
        return f"{obj.api_key[:8]}..."

    api_key_short.short_description = "API Key"

    def usage_display(self, obj):
        percentage = (
            (obj.current_month_usage / obj.monthly_message_limit) * 100
            if obj.monthly_message_limit > 0
            else 0
        )
        color = "red" if percentage > 80 else "orange" if percentage > 60 else "green"
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color,
            obj.current_month_usage,
            obj.monthly_message_limit,
            int(percentage),
        )

    usage_display.short_description = "Usage This Month"


@admin.register(ChatbotConfiguration)
class ChatbotConfigurationAdmin(admin.ModelAdmin):
    list_display = ("client", "title", "model", "temperature")
    list_filter = ("model",)
    search_fields = ("client__name", "title")

    fieldsets = (
        ("Basic Configuration", {"fields": ("client", "title", "welcome_message")}),
        (
            "AI Configuration",
            {"fields": ("system_prompt", "model", "temperature", "max_tokens")},
        ),
        ("Appearance", {"fields": ("primary_color", "position", "theme")}),
        ("Knowledge Base", {"fields": ("knowledge_content", "knowledge_file")}),
        (
            "Rate Limiting",
            {"fields": ("messages_per_session", "tool_calls_per_session")},
        ),
    )


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id_short",
        "client",
        "domain",
        "message_count",
        "started_at",
        "session_status",
    )
    list_filter = ("started_at", "client")
    search_fields = ("client__name", "domain")
    readonly_fields = ("id", "started_at")

    def id_short(self, obj):
        return str(obj.id)[:8]

    id_short.short_description = "Session ID"

    def session_status(self, obj):
        if obj.ended_at:
            duration = obj.ended_at - obj.started_at
            return f"Ended ({duration.total_seconds():.0f}s)"
        return format_html('<span style="color: green;">Active</span>')

    session_status.short_description = "Status"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "session_short",
        "message_preview",
        "response_time_ms",
        "created_at",
    )
    list_filter = ("created_at", "session__client")
    search_fields = ("message", "response")
    readonly_fields = ("created_at",)

    def session_short(self, obj):
        return f"{obj.session.client.name} - {str(obj.session.id)[:8]}"

    session_short.short_description = "Session"

    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message

    message_preview.short_description = "Message"
