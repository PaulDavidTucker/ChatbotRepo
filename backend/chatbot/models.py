import uuid
import secrets
from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    """Represents a client/domain using the chatbot widget"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True)
    api_key = models.CharField(max_length=64, unique=True, editable=False)

    # Configuration (stored as JSON)
    config = models.JSONField(default=dict, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="clients"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.domain})"

    @staticmethod
    def generate_api_key():
        """Generate a secure API key"""
        return secrets.token_urlsafe(48)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)


class ChatSession(models.Model):
    """Track chat sessions for analytics"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="sessions"
    )
    session_id = models.CharField(max_length=255)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    message_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["client", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.client.name} - {self.session_id[:16]}"
