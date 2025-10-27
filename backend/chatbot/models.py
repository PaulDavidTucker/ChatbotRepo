from django.db import models
import secrets
import uuid


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    api_key = models.CharField(max_length=64, unique=True)
    allowed_domains = models.JSONField(
        default=list, help_text="List of allowed domains"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Usage tracking
    monthly_message_limit = models.IntegerField(default=1000)
    current_month_usage = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.api_key[:8]}...)"


class ChatbotConfiguration(models.Model):
    client = models.OneToOneField(
        Client, on_delete=models.CASCADE, related_name="config"
    )
    title = models.CharField(max_length=100, default="AI Assistant")
    welcome_message = models.TextField(default="Hello! How can I help you?")
    system_prompt = models.TextField(default="You are a helpful assistant.")
    model = models.CharField(max_length=50, default="gpt-4o-mini")
    temperature = models.FloatField(default=0.1)
    max_tokens = models.IntegerField(default=1000)

    # Styling
    primary_color = models.CharField(max_length=7, default="#007bff")
    position = models.CharField(max_length=20, default="bottom-right")
    theme = models.CharField(max_length=20, default="default")

    # Knowledge base
    knowledge_content = models.TextField(blank=True)
    knowledge_file = models.FileField(upload_to="knowledge/", blank=True, null=True)

    # Rate limiting
    messages_per_session = models.IntegerField(default=15)
    tool_calls_per_session = models.IntegerField(default=3)

    def __str__(self):
        return f"Config for {self.client.name}"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    domain = models.CharField(max_length=255)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    message_count = models.IntegerField(default=0)
    tool_calls_count = models.IntegerField(default=0)


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    response_time_ms = models.IntegerField(default=0)
