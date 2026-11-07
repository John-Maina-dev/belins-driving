from django.db import models
from django.core.exceptions import ValidationError

class SiteSettings(models.Model):
    """
    Singleton model for global website configuration, branding, contact info,
    and hero section contents.
    """
    school_name = models.CharField(max_length=150, default="Belings Driving School")
    tagline = models.CharField(
        max_length=255,
        default="Shaping Confident, Competent & Defensive Drivers Across Kenya"
    )
    logo = models.ImageField(upload_to='branding/', blank=True, null=True, help_text="Upload brand logo (leave empty to use text brand placeholder)")
    phone = models.CharField(max_length=30, default="+254 700 123 456")
    phone_secondary = models.CharField(max_length=30, blank=True, default="+254 733 987 654")
    email = models.EmailField(default="info@belingsdriving.co.ke")
    address = models.CharField(
        max_length=255,
        default="Belings Towers, 3rd Floor, Moi Avenue / Commercial Street, Nairobi, Kenya"
    )
    whatsapp_number = models.CharField(
        max_length=30,
        default="254700123456",
        help_text="Format without + or spaces, e.g. 254700123456"
    )
    opening_hours = models.CharField(
        max_length=255,
        default="Mon - Fri: 7:00 AM - 6:30 PM | Sat: 8:00 AM - 4:00 PM | Sun: Closed"
    )
    hero_title = models.CharField(
        max_length=200,
        default="Drive with Confidence. Pass Your Test on First Attempt."
    )
    hero_subtitle = models.TextField(
        default="NTSA-accredited driving institution offering category A, B, and C curriculum with modern dual-pedal vehicles, certified professional instructors, and personalized driving schedules."
    )
    hero_image = models.ImageField(upload_to='branding/', blank=True, null=True)
    hero_cta_text = models.CharField(max_length=50, default="Enroll Now")
    hero_cta_link = models.CharField(max_length=100, default="/enroll/")

    # About Us Story, Mission & Vision
    about_story = models.TextField(
        default="Established with a commitment to road safety and driving excellence, Belings Driving School has equipped thousands of Kenyan drivers with defensive motoring skills, sound road ethics, and technical proficiency. We bridge the gap between passing the driving test and becoming a genuinely competent driver for life."
    )
    mission = models.TextField(
        default="To deliver world-class, accessible driver training grounded in safety, defensive road skills, and integrity, fostering accident-free roads across East Africa."
    )
    vision = models.TextField(
        default="To be Kenya's most trusted, innovative, and results-oriented driving academy recognized for exceptional pass rates and exemplary road safety ambassadors."
    )
    ntsa_accreditation_note = models.CharField(
        max_length=255,
        default="Fully Accredited by the National Transport and Safety Authority (NTSA) under License BDS-NTSA-2024-K."
    )

    # Social links
    facebook_url = models.URLField(blank=True, default="https://facebook.com/belingsdrivingschool")
    twitter_url = models.URLField(blank=True, default="https://twitter.com/belingsdriving")
    instagram_url = models.URLField(blank=True, default="https://instagram.com/belingsdrivingschool")
    linkedin_url = models.URLField(blank=True, default="https://linkedin.com/company/belingsdrivingschool")
    youtube_url = models.URLField(blank=True, default="https://youtube.com/@belingsdrivingschool")

    # Key statistics counters
    stat_students = models.CharField(max_length=50, default="12,500+", help_text="e.g. 12,500+")
    stat_pass_rate = models.CharField(max_length=50, default="98.5%", help_text="e.g. 98.5%")
    stat_experience_years = models.CharField(max_length=50, default="12+", help_text="e.g. 12+")
    stat_certified_instructors = models.CharField(max_length=50, default="24+", help_text="e.g. 24+")

    # Google Map Embed URL
    map_embed_url = models.TextField(
        blank=True,
        default="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988.819917806085!2d36.8194443!3d-1.2833333!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x182f10d650b299e5%3A0xb3a826bc59bf6a96!2sNairobi%2C%20Kenya!5e0!3m2!1sen!2ske!4v1700000000000!5m2!1sen!2ske",
        help_text="Embed link from Google Maps iframe src"
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return f"{self.school_name} Configuration"

    def clean(self):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("There can only be one SiteSettings instance.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Testimonial(models.Model):
    name = models.CharField(max_length=120)
    course_taken = models.CharField(max_length=150, help_text="e.g. Category B (Light Vehicle) Graduate")
    rating = models.PositiveSmallIntegerField(default=5, choices=[(i, f"{i} Stars") for i in range(1, 6)])
    quote = models.TextField()
    avatar = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_featured = models.BooleanField(default=True, help_text="Show on homepage carousel")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return f"{self.name} ({self.rating} stars) - {self.course_taken}"


class GalleryImage(models.Model):
    CATEGORY_CHOICES = [
        ('practical', 'Practical Lessons'),
        ('fleet', 'Our Fleet & Vehicles'),
        ('theory', 'Theory & Classroom'),
        ('instructors', 'Instructors & Staff'),
        ('graduation', 'Graduates & Test Days'),
    ]

    title = models.CharField(max_length=150)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='practical')
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General Driving Inquiries'),
        ('enrollment', 'Enrollment & Admission'),
        ('fees', 'Fees, Installments & Payment'),
        ('ntsa', 'NTSA Requirements & Test Booking'),
        ('practical', 'Practical Lessons & Schedule'),
    ]

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"
