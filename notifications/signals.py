from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

User = get_user_model()

@receiver(post_save, sender='host.Proposal')
def proposal_notification(sender, instance, created, **kwargs):
    if created:  # Submitted
        Notification.objects.create(
            recipient=instance.event.host,
            notification_type='proposal_submitted',
            message=f'New proposal received for "{instance.event.name}" from {instance.planner.full_name}. Amount: ₹{instance.amount}',
            related_object_id=instance.id,
            related_model='host.proposal'
        )
        # Optional email
        send_mail(
            'New Proposal Received',
            f'Check your dashboard for the proposal on "{instance.event.name}".',
            settings.DEFAULT_FROM_EMAIL,
            [instance.event.host.email],
            fail_silently=True,
        )
    else:  # Updated; check if status changed to accepted
        if instance.status == 'accepted' and kwargs.get('update_fields', {}).get('status') == 'accepted':
            Notification.objects.create(
                recipient=instance.planner,
                notification_type='proposal_accepted',
                message=f'Your proposal for "{instance.event.name}" has been accepted by {instance.event.host.full_name}!',
                related_object_id=instance.id,
                related_model='host.proposal'
            )
            send_mail(
                'Proposal Accepted',
                f'Congratulations! Contract secured for "{instance.event.name}". Proceed to chat for negotiation.',
                settings.DEFAULT_FROM_EMAIL,
                [instance.planner.email],
                fail_silently=True,
            )

@receiver(post_save, sender='guest.Booking')
def booking_notification(sender, instance, created, **kwargs):
    if created:
        # Notify guest
        Notification.objects.create(
            recipient=instance.guest,
            notification_type='booking_created',
            message=f'Booking confirmed for "{instance.event.name}". Booking ID: {instance.booking_id}. Check e-ticket.',
            related_object_id=instance.id,
            related_model='guest.booking'
        )
        send_mail(
            'Booking Confirmation',
            f'Thank you for booking "{instance.event.name}". Your e-ticket is ready.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.guest.email],
            fail_silently=True,
        )
        # Notify host
        Notification.objects.create(
            recipient=instance.event.host,
            notification_type='booking_created',
            message=f'New guest {instance.guest.full_name} joined "{instance.event.name}". Total: {instance.total_amount}',
            related_object_id=instance.id,
            related_model='guest.booking'
        )
        send_mail(
            'New Guest Booking',
            f'{instance.guest.full_name} has booked for your event "{instance.event.name}".',
            settings.DEFAULT_FROM_EMAIL,
            [instance.event.host.email],
            fail_silently=True,
        )

@receiver(post_save, sender='host.Event')
def event_notification(sender, instance, created, **kwargs):
    if created:
        # Notify admin (superusers)
        for admin in User.objects.filter(is_superuser=True):
            Notification.objects.create(
                recipient=admin,
                notification_type='event_created',
                message=f'New event created: "{instance.name}" by {instance.host.full_name}. Review in admin panel.',
                related_object_id=instance.id,
                related_model='host.event'
            )
            send_mail(
                'New Event Alert',
                f'A new event "{instance.name}" has been added to the platform.',
                settings.DEFAULT_FROM_EMAIL,
                [admin.email],
                fail_silently=True,
            )