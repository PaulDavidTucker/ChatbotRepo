# backend/chatbot/tools.py
from langchain.tools import tool
from pydantic import BaseModel, Field, validator
from django.core.mail import send_mail
import re


class EmailInput(BaseModel):
    to: str = Field(description="The recipient's email address.")
    subject: str = Field(description="The subject of the email.")
    body: str = Field(description="The body of the email.")

    @validator("to")
    def validate_email(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email address")
        # Optional: Allowlist domains (e.g., only @example.com)
        # if not v.endswith('@example.com'):
        #     raise ValueError("Email domain not allowed")
        return v


class CalendarInput(BaseModel):
    bookerEmail: str = Field(description="The client's email address.")
    platform: str = Field(description="The platform (e.g., Zoom, Teams).")

    @validator("bookerEmail")
    def validate_email(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email address")
        return v


@tool
async def send_email(to: str, subject: str, body: str) -> str:
    """Sends an email to a user. Use when the user requests to send information via email."""
    input_data = EmailInput(to=to, subject=subject, body=body)  # Validates
    try:
        send_mail(subject, body, "info@repsandrevenue.com", [to])
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"


@tool
async def book_appointment(bookerEmail: str, platform: str) -> str:
    """Books a calendar appointment via Calendly. Use when the user wants to schedule a meeting."""
    input_data = CalendarInput(bookerEmail=bookerEmail, platform=platform)  # Validates
    try:
        print(f"Mock booking for {bookerEmail} on {platform}")
        return f"Appointment booked for {bookerEmail} on {platform}! (Mock—real integration coming soon)"
    except Exception as e:
        return f"Failed to book appointment: {str(e)}"
