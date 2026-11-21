from django.contrib import admin

from .models import ChatMessage, Feedback, SupportTicket


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "role", "user", "intent", "order", "short_text")
    list_filter = ("role", "intent")
    search_fields = ("text", "session_key", "user__username")

    def short_text(self, obj):
        return obj.text[:60]


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "user", "order", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status",)
    search_fields = ("subject", "description", "user__username")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "helpful", "user", "created_at")
    list_filter = ("helpful",)
