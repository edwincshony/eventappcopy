from django.db import models
from django.conf import settings
from django.apps import apps
from django.utils import timezone

class Notification(models.Model):
    TYPE_CHOICES = [
        ('proposal_submitted', 'Proposal Submitted'),
        ('proposal_accepted', 'Proposal Accepted'),
        ('booking_created', 'New Booking'),
        ('event_created', 'New Event'),
        ('general', 'General Alert'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    related_object_id = models.PositiveIntegerField(null=True, blank=True)  # e.g., Proposal/Booking ID
    related_model = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'host.proposal'
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.username} - {self.created_at}"

    @property
    def related_object(self):
        if self.related_object_id and self.related_model:
            model_class = apps.get_model(self.related_model)
            return model_class.objects.get(id=self.related_object_id)
        return None