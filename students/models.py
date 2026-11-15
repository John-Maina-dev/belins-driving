from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from courses.models import Course, Branch, Vehicle
from instructors.models import Instructor
from .validators import validate_age_18_plus, calculate_age

class Student(models.Model):
    STATUS_PENDING_APPROVAL = 'PENDING_APPROVAL'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_PENDING_APPROVAL, 'Pending Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Graduated / Completed'),
        # Backward-compatible choices
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('enrolled', 'Enrolled & Active'),
        ('rejected', 'Rejected'),
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

    PAYMENT_METHOD_CHOICES = [
        ('', '-- Select Payment Method --'),
        ('MPESA', 'M-Pesa'),
        ('CASH', 'Cash'),
        ('BANK', 'Bank Transfer'),
        ('CARD', 'Debit / Credit Card'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='enrollments'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=25, help_text="e.g. 0712 345 678 or +254 712 345 678")
    id_number = models.CharField(max_length=50, help_text="National ID, Passport, or Birth Certificate No.")
    date_of_birth = models.DateField(null=True, blank=False, help_text="Required: Date of birth (Age 18+ only)")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='students')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True, related_name='students')
    start_date = models.DateField(null=True, blank=True, help_text="Course start date")
    preferred_schedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='morning')
    preferred_branch = models.CharField(max_length=100, default='Main Campus - Nairobi', help_text="Preferred training branch (name)")
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Agreed course fee in KES (defaults to course fee)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, help_text="Fee discount in KES")
    discount_reason = models.CharField(max_length=255, blank=True, default="", help_text="Reason for fee discount")
    initial_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, help_text="First payment received at enrollment")
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, blank=True, default="")
    payment_reference = models.CharField(max_length=100, blank=True, default="", help_text="M-Pesa code or receipt reference")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING_APPROVAL)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_enrollments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Internal staff notes, medical remarks, or special requests")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Enrollment'
        verbose_name_plural = 'Student Enrollments'

    def clean(self):
        super().clean()
        if not self.date_of_birth:
            raise ValidationError({'date_of_birth': "Date of birth is required."})

        today = timezone.localdate()
        if self.date_of_birth > today:
            raise ValidationError({'date_of_birth': "Date of birth cannot be in the future."})

        age = calculate_age(self.date_of_birth, today)
        if age < 18:
            # Allow existing records if date of birth was unchanged
            if self.pk:
                orig = Student.objects.filter(pk=self.pk).values('date_of_birth').first()
                if orig and orig.get('date_of_birth') == self.date_of_birth:
                    return
            raise ValidationError({'date_of_birth': "You must be 18 years or older to register."})

        # Validate that course is offered at chosen branch if both branch and course are set
        if self.branch_id and self.course_id and self.course.branches.exists():
            if not self.course.branches.filter(pk=self.branch_id).exists():
                raise ValidationError({'course': f"The course '{self.course.name}' is not offered at {self.branch.name}."})

    def save(self, *args, **kwargs):
        self.clean()
        if self.branch_id and self.branch:
            self.preferred_branch = self.branch.name
        if self.total_fee is None and self.course_id:
            self.total_fee = self.course.fee
        super().save(*args, **kwargs)

    @property
    def effective_fee(self):
        base = self.total_fee if self.total_fee is not None else (self.course.fee if self.course_id else 0)
        disc = self.discount_amount or 0
        return max(0, base - disc)

    @property
    def balance_due(self):
        paid = self.initial_payment_amount or 0
        return max(0, self.effective_fee - paid)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.course.name}) - {self.get_status_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_approved(self):
        return self.status in [self.STATUS_APPROVED, 'approved', 'enrolled', self.STATUS_COMPLETED]

    @property
    def is_pending(self):
        return self.status in [self.STATUS_PENDING_APPROVAL, 'pending']

    @property
    def verified_practical_hours(self):
        """Total verified practical hours officially completed by student."""
        bookings = self.bookings.filter(status='VERIFIED', lesson_type='PRACTICAL')
        return sum(b.duration_hours for b in bookings)

    @property
    def verified_theory_hours(self):
        """Total verified theory hours officially completed by student."""
        bookings = self.bookings.filter(status='VERIFIED', lesson_type='THEORY')
        return sum(b.duration_hours for b in bookings)

    @property
    def reserved_practical_hours(self):
        """Practical hours reserved by SCHEDULED, COMPLETED, or VERIFIED bookings."""
        bookings = self.bookings.filter(
            status__in=['SCHEDULED', 'COMPLETED', 'VERIFIED'],
            lesson_type='PRACTICAL'
        )
        return sum(b.duration_hours for b in bookings)

    @property
    def reserved_theory_hours(self):
        """Theory hours reserved by SCHEDULED, COMPLETED, or VERIFIED bookings."""
        bookings = self.bookings.filter(
            status__in=['SCHEDULED', 'COMPLETED', 'VERIFIED'],
            lesson_type='THEORY'
        )
        return sum(b.duration_hours for b in bookings)

    @property
    def remaining_practical_hours(self):
        return max(0.0, float(self.course.practical_hours) - self.verified_practical_hours)

    @property
    def remaining_theory_hours(self):
        return max(0.0, float(self.course.theory_hours) - self.verified_theory_hours)


class LessonBooking(models.Model):
    LESSON_TYPE_CHOICES = [
        ('PRACTICAL', 'Practical Driving Lesson'),
        ('THEORY', 'Classroom Theory Lecture'),
    ]
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed (Awaiting Admin Verification)'),
        ('VERIFIED', 'Verified'),
        ('CANCELLED', 'Cancelled by Student'),
        ('NO_SHOW', 'Student No-Show'),
        ('REJECTED', 'Disputed / Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='bookings')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='bookings')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='bookings')
    instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    lesson_type = models.CharField(max_length=15, choices=LESSON_TYPE_CHOICES, default='PRACTICAL')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    instructor_notes = models.TextField(blank=True, help_text="Instructor feedback, maneuvers covered, or areas to improve")
    student_notes = models.TextField(blank=True, help_text="Special requests or questions from student")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_lessons'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason when verification is declined")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = 'Lesson Booking'
        verbose_name_plural = 'Lesson Bookings'

    def __str__(self):
        return f"{self.student.full_name} - {self.get_lesson_type_display()} on {self.date} at {self.start_time}"

    @property
    def duration_hours(self):
        from datetime import datetime
        dummy_date = datetime(2000, 1, 1)
        t1 = datetime.combine(dummy_date, self.start_time)
        t2 = datetime.combine(dummy_date, self.end_time)
        diff = (t2 - t1).total_seconds() / 3600.0
        return max(diff, 1.0)


# Alias for explicit Enrollment model references
Enrollment = Student

