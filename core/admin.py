from django.contrib import admin

from .models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("question", "answer", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("document_name", "created_at", "updated_at")
    search_fields = ("document_name", "extracted_text")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "created_at")
    search_fields = ("question", "answer", "session__document_name")
    readonly_fields = ("created_at",)
