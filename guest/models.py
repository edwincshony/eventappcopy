from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    event = models.ForeignKey('host.Event', on_delete=models.CASCADE, related_name='bookings')
    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ticket_quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # e.g., event.ticket_price * quantity; assume fixed per event
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='confirmed')
    qr_code = models.ImageField(upload_to='bookings/', blank=True, null=True)  # Placeholder; generate in save
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.booking_id} for {self.event.name} by {self.guest.username}"

    def save(self, *args, **kwargs):
        # Placeholder QR generation (real: use qrcode; here, skip or text-based)
        super().save(*args, **kwargs)
        if not self.qr_code:
            # Simple text QR sim; in prod, generate image
            pass  # Add logic if qrcode installed

    class Meta:
        ordering = ['-created_at']