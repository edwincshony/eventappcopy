from django.db import models
from django.conf import settings
from django.utils import timezone


class Event(models.Model):
    NEEDS_CHOICES = [
        ('catering', 'Catering'),
        ('decorations', 'Decorations'),
        ('photography', 'Photography'),
        ('music', 'Music/DJ'),
        ('venue', 'Venue Setup'),
        ('other', 'Other'),
    ]
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    guest_count = models.PositiveIntegerField()
    needs = models.CharField(max_length=255, blank=True)
   
    banner = models.ImageField(upload_to='events/', blank=True, null=True)
    venue_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.host.username}"

    class Meta:
        ordering = ['-created_at']

class Proposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='proposals')
    planner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    services = models.TextField()  # e.g., "Catering + Decorations"
    timeline = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Proposal for {self.event.name} by {self.planner.username}"