from django.db import models
from courses.models import Course

class Student(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('enrolled', 'Enrolled & Active'),
        ('completed', 'Graduated / Completed'),
        ('rejected', 'Rejected / Cancelled'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    SCHEDULE_CHOICES = [
        ('morning', 'Morning (8:00 AM - 11:00 AM)'),
        ('afternoon', 'Afternoon (1:00 PM - 4:00 PM)'),
        ('evening', 'Evening (4:30 PM - 7:00 PM)'),
        ('weekend', 'Weekend Intensive (Sat 8:00 AM - 4:00 PM)'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=25, help_text="e.g. 0712 345 678 or +254 712 345 678")
    id_number = models.CharField(max_length=50, help_text="National ID, Passport, or Birth Certificate No.")
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='students')
    preferred_schedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='morning')
    preferred_branch = models.CharField(max_length=100, default='Main Campus - Nairobi', help_text="Preferred training branch")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text="Internal staff notes, medical remarks, or special requests")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Enrollment'
        verbose_name_plural = 'Student Enrollments'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.course.name}) - {self.get_status_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

