from django.db import models
from django.conf import settings
from django.utils import timezone

class Room(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    name = models.CharField(max_length=255, blank=True)  # e.g., "Event Negotiation"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.id} - {', '.join([p.username for p in self.participants.all()])}"

    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    class Meta:
        ordering = ['timestamp']