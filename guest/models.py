from django.db import models
from django.conf import settings
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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='confirmed')
    qrcode = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_id} for {self.event.name} by {self.guest.username}"

    def generate_qr_code(self):
        """Generate and attach a QR code image for this booking"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Encode booking ID into the QR
        qr.add_data(str(self.booking_id))
        qr.make(fit=True)

        # Create QR code image (Pillow Image object)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        # Prepare a white canvas
        canvas = Image.new('RGB', (300, 300), 'white')

        # Calculate center position for QR image
        qr_width, qr_height = qr_img.size
        canvas_width, canvas_height = canvas.size
        pos = ((canvas_width - qr_width) // 2, (canvas_height - qr_height) // 2)

        # ✅ Correct paste call — Pillow can now determine region
        canvas.paste(qr_img, pos)

        # Save the canvas as PNG to a BytesIO buffer
        buffer = BytesIO()
        canvas.save(buffer, format='PNG')
        buffer.seek(0)

        # Use correct attribute name
        filename = f'qr_code_{self.booking_id}.png'
        self.qrcode.save(filename, File(buffer), save=False)

        buffer.close()
        canvas.close()

    def save(self, *args, **kwargs):
        """Ensure QR code is generated when saving (optional auto behavior)"""
        super().save(*args, **kwargs)
        if not self.qrcode:
            self.generate_qr_code()
            super().save(update_fields=['qrcode'])
