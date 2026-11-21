from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Customer"
        BOT = "bot", "Bot"

    session_key = models.CharField(max_length=40, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="chat_messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    text = models.TextField(max_length=2000)
    intent = models.CharField(max_length=40, blank=True)
    order = models.ForeignKey("orders.Order", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="chat_messages")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.text[:40]}"


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_tickets")
    order = models.ForeignKey("orders.Order", null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="support_tickets")
    subject = models.CharField(max_length=120)
    description = models.TextField(max_length=1000)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket #{self.pk}: {self.subject}"


class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="chat_feedback")
    session_key = models.CharField(max_length=40, blank=True)
    helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "feedback"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Helpful: {self.helpful}"
