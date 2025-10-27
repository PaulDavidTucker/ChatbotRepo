import json
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from django.conf import settings
from .models import Client, ChatbotConfiguration, ChatSession, ChatMessage
from .tools import send_email, book_appointment
import os
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
        self.client, self.config = await self.get_client_config(
            self.api_key, self.domain
        )

        if not self.client:
            await self.close(code=4003)  # Forbidden
            return

        # Create session
        self.session = await self.create_session()
        self.chat_history = []

        # Initialize agent
        await self.initialize_agent()

        await self.accept()

        # Send welcome message
        await self.send(
            text_data=json.dumps(
                {
                    "type": "welcome",
                    "message": self.config.welcome_message,
                    "sender": "bot",
                }
            )
        )

    @database_sync_to_async
    def get_client_config(self, api_key, domain):
        try:
            client = Client.objects.get(api_key=api_key, is_active=True)

            # Check domain restriction
            if client.allowed_domains and domain not in client.allowed_domains:
                return None, None

            # Check usage limits
            if client.current_month_usage >= client.monthly_message_limit:
                return None, None

            config = ChatbotConfiguration.objects.get(client=client)
            return client, config
        except (Client.DoesNotExist, ChatbotConfiguration.DoesNotExist):
            return None, None

    @database_sync_to_async
    def create_session(self):
        return ChatSession.objects.create(
            client=self.client,
            domain=self.domain,
            user_ip=self.get_client_ip(),
            user_agent=dict(self.scope.get("headers", {}))
            .get(b"user-agent", b"")
            .decode(),
        )

    def get_client_ip(self):
        x_forwarded_for = dict(self.scope.get("headers", {})).get(b"x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.decode().split(",")[0]
        return self.scope.get("client", ["unknown"])[0]

    async def initialize_agent(self):
        env = environ.Env()
        environ.Env.read_env(os.path.join(settings.BASE_DIR, ".env"))
        key = env("OPENAI_API_KEY", default=os.environ.get("OPENAI_API_KEY"))

        # Load knowledge content
        knowledge_content = self.config.knowledge_content
        if self.config.knowledge_file:
            try:
                with open(self.config.knowledge_file.path, "r") as f:
                    knowledge_content += f"\n\n" + f.read().strip()
            except Exception as e:
                print(f"Error loading knowledge file: {e}")

        model = init_chat_model(
            model=f"openai:{self.config.model}",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            reasoning_effort="low",
            timeout=30,
            max_retries=2,
            api_key=key,
        )

        tools = [send_email, book_appointment]

        system_prompt = (
            f"{self.config.system_prompt}\n\nKnowledge Base:\n{knowledge_content}"
        )

        self.agent = create_agent(model, tools, system_prompt=system_prompt)

    async def disconnect(self, close_code):
        if hasattr(self, "session"):
            await self.end_session()

    @database_sync_to_async
    def end_session(self):
        from django.utils import timezone

        self.session.ended_at = timezone.now()
        self.session.message_count = len(
            [msg for msg in self.chat_history if msg["sender"] == "user"]
        )
        self.session.save()

    async def receive(self, text_data):
        start_time = time.time()
        data = json.loads(text_data)
        user_message = data.get("message", "")

        # Check session limits
        user_message_count = len(
            [msg for msg in self.chat_history if msg["sender"] == "user"]
        )

        if user_message_count >= self.config.messages_per_session:
            await self.send(
                text_data=json.dumps(
                    {
                        "message": f"You've reached the message limit ({self.config.messages_per_session} per session). Please start a new session.",
                        "sender": "bot",
                    }
                )
            )
            return

        if self.session.tool_calls_count >= self.config.tool_calls_per_session:
            await self.send(
                text_data=json.dumps(
                    {
                        "message": f"You've reached the tool usage limit ({self.config.tool_calls_per_session} per session).",
                        "sender": "bot",
                    }
                )
            )
            return

        # Update usage
        await self.increment_usage()

        # Prepare history
        history_messages = []
        for msg in self.chat_history:
            if msg["sender"] == "user":
                history_messages.append(HumanMessage(content=msg["text"]))
            else:
                history_messages.append(AIMessage(content=msg["text"]))

        self.chat_history.append({"sender": "user", "text": user_message})

        try:
            await self.send(text_data=json.dumps({"type": "start"}))

            response_text = ""

            async for chunk in self.agent.astream(
                {"messages": history_messages + [HumanMessage(content=user_message)]}
            ):
                if isinstance(chunk, dict):
                    if "actions" in chunk:
                        for action in chunk["actions"]:
                            await self.increment_tool_usage()

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

            await self.send(text_data=json.dumps({"type": "end"}))

            # Save conversation
            response_time = int((time.time() - start_time) * 1000)
            await self.save_message(user_message, response_text, response_time)

        except Exception as e:
            response_text = (
                "There was an issue with our bot! Please try reloading the page"
            )
            print(f"Error! {e}")
            await self.send(
                text_data=json.dumps({"message": response_text, "sender": "bot"})
            )

        self.chat_history.append({"sender": "bot", "text": response_text})

    @database_sync_to_async
    def increment_usage(self):
        self.client.current_month_usage += 1
        self.client.save()

    @database_sync_to_async
    def increment_tool_usage(self):
        self.session.tool_calls_count += 1
        self.session.save()

    @database_sync_to_async
    def save_message(self, message, response, response_time_ms):
        return ChatMessage.objects.create(
            session=self.session,
            message=message,
            response=response,
            response_time_ms=response_time_ms,
        )
