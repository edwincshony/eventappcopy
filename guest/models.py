from django.db import models
from django.conf import settings
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import uuid


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    guest = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    event = models.ForeignKey(
        'host.Event',
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    ticket_quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    qrcode = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # new fields
    is_used = models.BooleanField(default=False)
    scanned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_id} for {self.event.name} by {self.guest.username}"

    def mark_as_used(self):
        """Mark QR as used once successfully scanned."""
        self.is_used = True
        self.scanned_at = timezone.now()
        self.save(update_fields=['is_used', 'scanned_at'])

    def generate_qr_code(self):
        """Generate and attach a QR code image for this booking"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(str(self.booking_id))
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        canvas = Image.new('RGB', (300, 300), 'white')

        qr_width, qr_height = qr_img.size
        pos = ((300 - qr_width) // 2, (300 - qr_height) // 2)
        canvas.paste(qr_img, pos)

        buffer = BytesIO()
        canvas.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f'qr_code_{self.booking_id}.png'
        self.qrcode.save(filename, File(buffer), save=False)

        buffer.close()
        canvas.close()

    def save(self, *args, **kwargs):
        # Check if this is a new instance (being created for the first time)
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.qrcode:
            self.generate_qr_code()
            super().save(update_fields=['qrcode'])

