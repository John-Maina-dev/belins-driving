from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_SUPER_ADMIN = 'SUPER_ADMIN'
    ROLE_ADMIN = 'ADMIN'
    ROLE_INSTRUCTOR = 'INSTRUCTOR'
    ROLE_STUDENT = 'STUDENT'
    ROLE_RECEPTIONIST = 'RECEPTIONIST'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Administrator'),
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_INSTRUCTOR, 'Instructor'),
        (ROLE_STUDENT, 'Student'),
        (ROLE_RECEPTIONIST, 'Receptionist / Cashier'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.user.is_superuser or self.role == self.ROLE_SUPER_ADMIN

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_management_authorized(self):
        return self.user.is_superuser or self.role in [self.ROLE_SUPER_ADMIN, self.ROLE_ADMIN]


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        initial_role = UserProfile.ROLE_SUPER_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT
        UserProfile.objects.create(user=instance, role=initial_role)
    else:
        if hasattr(instance, 'profile'):
            if instance.is_superuser and instance.profile.role != UserProfile.ROLE_SUPER_ADMIN:
                instance.profile.role = UserProfile.ROLE_SUPER_ADMIN
                instance.profile.save()
        else:
            initial_role = UserProfile.ROLE_SUPER_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT
            UserProfile.objects.create(user=instance, role=initial_role)
