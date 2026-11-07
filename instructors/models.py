from django.db import models
from website.models import safe_upload_path, validate_image_file

class Instructor(models.Model):
    full_name = models.CharField(max_length=150)
    title = models.CharField(max_length=150, help_text="e.g. Chief Driving Instructor / Defensive Driving Specialist")
    license_categories = models.CharField(max_length=100, default="Category A, B & C", help_text="Categories certified to teach")
    experience_years = models.PositiveIntegerField(default=5, help_text="Years of driving instruction experience")
    bio = models.TextField(help_text="Professional background and qualifications")
    photo = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    ntsa_cert_number = models.CharField(max_length=100, blank=True, help_text="NTSA Instructor License / Certification ID")
    is_featured = models.BooleanField(default=True, help_text="Show in homepage instructors preview")
    is_active = models.BooleanField(default=True, help_text="Display on public website")
    order = models.PositiveIntegerField(default=0, help_text="Display ordering")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'full_name']
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructors'

    def __str__(self):
        return f"{self.full_name} ({self.title})"

