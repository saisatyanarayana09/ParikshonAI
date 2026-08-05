import uuid

from django.contrib.auth.models import User
from django.db import models
from pgvector.django import VectorField


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    dob = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Signed-in user — null for anonymous sessions
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name="sessions"
    )
    # Django session key to identify anonymous users
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    document_name = models.CharField(max_length=255)
    extracted_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.document_name

    @property
    def message_count(self):
        return self.messages.count()


class DocumentChunk(models.Model):
    """A document passage and its embedding, stored in the application database."""

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=384)

    class Meta:
        ordering = ["chunk_index"]
        constraints = [
            models.UniqueConstraint(fields=["session", "chunk_index"], name="unique_session_chunk_index"),
        ]

    def __str__(self):
        return f"{self.session.document_name} — chunk {self.chunk_index}"


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.question[:80]
