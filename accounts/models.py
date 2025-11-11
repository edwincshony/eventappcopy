from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('planner', 'Planner'),
        ('guest', 'Guest'),
        ('host', 'Host'),
    ]
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, blank=True, null=True,
        help_text="User role (None for superusers/admins)"
    )
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True, blank=False)  # Enforced required in forms
    mobile_number = models.CharField(max_length=10, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_approved = models.BooleanField(default=False, help_text="For planners/guests only")

    def __str__(self):
        return self.username