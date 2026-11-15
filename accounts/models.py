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

    APPROVAL_PENDING = 'PENDING'
    APPROVAL_APPROVED = 'APPROVED'
    APPROVAL_REJECTED = 'REJECTED'

    APPROVAL_CHOICES = [
        (APPROVAL_PENDING, 'Pending Approval'),
        (APPROVAL_APPROVED, 'Approved'),
        (APPROVAL_REJECTED, 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default=APPROVAL_PENDING,
        help_text="Account approval state: PENDING, APPROVED, or REJECTED"
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_profiles'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True, help_text="Required for student registrations (Age 18+ only)")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def clean(self):
        super().clean()
        if self.role == self.ROLE_STUDENT and self.date_of_birth:
            from students.validators import validate_age_18_plus
            validate_age_18_plus(self.date_of_birth)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) - {self.approval_status}"

    @property
    def is_super_admin(self):
        return self.user.is_superuser or self.role == self.ROLE_SUPER_ADMIN

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_management_authorized(self):
        return self.user.is_superuser or self.role in [self.ROLE_SUPER_ADMIN, self.ROLE_ADMIN]

    @property
    def is_approved(self):
        return self.user.is_superuser or self.approval_status == self.APPROVAL_APPROVED


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        initial_role = UserProfile.ROLE_SUPER_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT
        initial_status = UserProfile.APPROVAL_APPROVED if instance.is_superuser else UserProfile.APPROVAL_PENDING
        UserProfile.objects.create(user=instance, role=initial_role, approval_status=initial_status)
    else:
        if hasattr(instance, 'profile'):
            if instance.is_superuser:
                if instance.profile.role != UserProfile.ROLE_SUPER_ADMIN or instance.profile.approval_status != UserProfile.APPROVAL_APPROVED:
                    instance.profile.role = UserProfile.ROLE_SUPER_ADMIN
                    instance.profile.approval_status = UserProfile.APPROVAL_APPROVED
                    instance.profile.save()
        else:
            initial_role = UserProfile.ROLE_SUPER_ADMIN if instance.is_superuser else UserProfile.ROLE_STUDENT
            initial_status = UserProfile.APPROVAL_APPROVED if instance.is_superuser else UserProfile.APPROVAL_PENDING
            UserProfile.objects.create(user=instance, role=initial_role, approval_status=initial_status)
