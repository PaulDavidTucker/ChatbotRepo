import json
import time
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from django.conf import settings
from django.utils import timezone
from .models import Client, ChatSession
from .tools import send_email, book_appointment
import environ


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract client info from URL
        self.api_key = self.scope["url_route"]["kwargs"].get("api_key")
        self.domain = (
            self.scope["query_string"].decode().split("domain=")[1].split("&")[0]
            if "domain=" in self.scope["query_string"].decode()
            else "unknown"
        )

        # Validate client
        self.client = await self.get_client(self.api_key)

        if not self.client:
            await self.close(code=4003)  # Forbidden
            return

        # Get config from JSONField (with defaults)
        self.config = self.client.config or {}

        # Create session
        self.session = await self.create_session()
        self.chat_history = []

        # Initialize agent
        await self.initialize_agent()

        await self.accept()

        # Send welcome message
        welcome_msg = self.config.get(
            "welcome_message", "Hello! How can I help you today?"
        )
        await self.send(
            text_data=json.dumps(
                {"type": "welcome", "message": welcome_msg, "sender": "bot"}
            )
        )

    @database_sync_to_async
    def get_client(self, api_key):
        """Get and validate client"""
        try:
            client = Client.objects.get(api_key=api_key, is_active=True)
            return client
        except Client.DoesNotExist:
            print("Missing a client!")
            return None

    @database_sync_to_async
    def create_session(self):
        """Create a new chat session"""
        return ChatSession.objects.create(
            client=self.client,
            session_id=self.scope.get("session", {}).get("session_key", "unknown"),
        )

    def get_client_ip(self):
        """Extract client IP from headers"""
        x_forwarded_for = dict(self.scope.get("headers", {})).get(b"x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.decode().split(",")[0]
        return self.scope.get("client", ["unknown"])[0]

    async def initialize_agent(self):
        """Initialize the LangChain agent with configuration"""
        env = environ.Env()
        environ.Env.read_env(os.path.join(settings.BASE_DIR.parent, ".env"))
        key = env("OPENAI_API_KEY", default=os.environ.get("OPENAI_API_KEY"))

        # Get configuration with defaults
        model_name = self.config.get("model", "gpt-4o-mini")
        temperature = self.config.get("temperature", 0.1)
        max_tokens = self.config.get("max_tokens", 1000)
        system_prompt = self.config.get(
            "system_prompt", "You are a helpful AI assistant."
        )
        knowledge_content = self.config.get("knowledge_content", "")

        # Initialize model
        model = init_chat_model(
            model=f"openai:{model_name}",
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort="low",
            timeout=30,
            max_retries=2,
            api_key=key,
        )

        tools = [send_email, book_appointment]

        # Append knowledge base to system prompt if available
        full_system_prompt = system_prompt
        if knowledge_content:
            full_system_prompt += f"\n\nKnowledge Base:\n{knowledge_content}"

        self.agent = create_agent(model, tools, system_prompt=full_system_prompt)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnect"""
        if hasattr(self, "session"):
            await self.end_session()

    @database_sync_to_async
    def end_session(self):
        """Mark session as ended"""
        self.session.ended_at = timezone.now()
        self.session.message_count = len(
            [msg for msg in self.chat_history if msg["sender"] == "user"]
        )
        self.session.save()

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        start_time = time.time()
        data = json.loads(text_data)
        user_message = data.get("message", "")

        # Check session limits (with defaults from config)
        messages_per_session = self.config.get("messages_per_session", 50)
        user_message_count = len(
            [msg for msg in self.chat_history if msg["sender"] == "user"]
        )

        if user_message_count >= messages_per_session:
            await self.send(
                text_data=json.dumps(
                    {
                        "message": f"You've reached the message limit ({messages_per_session} per session). Please refresh to start a new session.",
                        "sender": "bot",
                    }
                )
            )
            return

        # Prepare conversation history
        history_messages = []
        for msg in self.chat_history:
            if msg["sender"] == "user":
                history_messages.append(HumanMessage(content=msg["text"]))
            else:
                history_messages.append(AIMessage(content=msg["text"]))

        self.chat_history.append({"sender": "user", "text": user_message})

        try:
            # Signal start of response
            await self.send(text_data=json.dumps({"type": "start"}))

            response_text = ""

            # Stream agent response
            async for chunk in self.agent.astream(
                {"messages": history_messages + [HumanMessage(content=user_message)]}
            ):
                if isinstance(chunk, dict):
                    # Handle tool calls
                    if "actions" in chunk:
                        for action in chunk["actions"]:
                            await self.increment_session_count()

                    # Handle message chunks
                    if "model" in chunk and "messages" in chunk["model"]:
                        for message in chunk["model"]["messages"]:
                            if hasattr(message, "content") and message.content:
                                chunk_content = message.content
                                response_text += chunk_content
                                await self.send(
                                    text_data=json.dumps(
                                        {"type": "chunk", "content": chunk_content}
                                    )
                                )

            # Signal end of response
            await self.send(text_data=json.dumps({"type": "end"}))

            # Update session message count
            await self.update_session_messages()

        except Exception as e:
            response_text = (
                "I encountered an error processing your request. Please try again."
            )
            print(f"Agent Error: {e}")
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": response_text, "sender": "bot"}
                )
            )

        self.chat_history.append({"sender": "bot", "text": response_text})

    @database_sync_to_async
    def increment_session_count(self):
        """Increment message count for the session"""
        self.session.message_count += 1
        self.session.save()

    @database_sync_to_async
    def update_session_messages(self):
        """Update the total message count"""
        self.session.message_count = len(
            [msg for msg in self.chat_history if msg["sender"] == "user"]
        )
        self.session.save()
