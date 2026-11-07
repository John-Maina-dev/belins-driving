import os
import uuid
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache

def safe_upload_path(instance, filename):
    """Generate safe, randomized UUID filename to prevent arbitrary file upload vulnerabilities."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.ico']:
        ext = '.jpg'
    return f"uploads/{uuid.uuid4().hex}{ext}"

def validate_image_file(file):
    """Validate image file format (allows any file size)."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.ico']:
        raise ValidationError("Unsupported format. Allowed formats: JPG, PNG, WEBP, ICO.")

def validate_hex_color(value):
    """Validate 3 or 6 digit hex color string (e.g. #020381)."""
    if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
        raise ValidationError("Invalid hex color code. Must be in format #RRGGBB or #RGB.")

def validate_kenyan_phone(value):
    """Validate Kenyan phone number format."""
    clean = re.sub(r'[\s\-]', '', value)
    if not re.match(r'^(?:\+254|0)[17]\d{8}$', clean):
        raise ValidationError("Enter a valid Kenyan phone number (e.g. 0712 345 678 or +254 700 123 456).")


class SiteSettings(models.Model):
    """
    Singleton configuration model storing all website branding, public content,
    contact details, SEO defaults, operational defaults, and maintenance mode.
    """
    CACHE_KEY = 'belings_site_settings_cache'

    FONT_HEADING_CHOICES = [
        ("'Roboto Slab', serif", "Roboto Slab (Classic Serif)"),
        ("'Inter', sans-serif", "Inter (Clean Modern Sans)"),
        ("'Montserrat', sans-serif", "Montserrat (Bold Geometric)"),
        ("'Poppins', sans-serif", "Poppins (Friendly Geometric)"),
        ("'Playfair Display', serif", "Playfair Display (Editorial Serif)"),
    ]

    FONT_BODY_CHOICES = [
        ("'Inter', sans-serif", "Inter (High Legibility Sans)"),
        ("'Open Sans', sans-serif", "Open Sans (Neutral Sans)"),
        ("'Roboto', sans-serif", "Roboto (Standard Sans)"),
        ("'Lato', sans-serif", "Lato (Warm Humanist)"),
    ]

    # 1. Branding & Identity
    school_name = models.CharField(max_length=150, default="Belings Driving School")
    tagline = models.CharField(max_length=255, default="Shaping Confident, Competent & Defensive Drivers Across Kenya")
    logo_light = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True, help_text="Logo for dark backgrounds")
    logo_dark = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True, help_text="Logo for light backgrounds")
    favicon = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    brand_primary = models.CharField(max_length=10, default="#020381", validators=[validate_hex_color], help_text="Primary Brand Navy")
    brand_secondary = models.CharField(max_length=10, default="#e9a825", validators=[validate_hex_color], help_text="Golden Accent / Buttons")
    brand_accent = models.CharField(max_length=10, default="#25D366", validators=[validate_hex_color], help_text="WhatsApp / Success Green")
    font_heading = models.CharField(max_length=100, choices=FONT_HEADING_CHOICES, default="'Roboto Slab', serif")
    font_body = models.CharField(max_length=100, choices=FONT_BODY_CHOICES, default="'Inter', sans-serif")

    # 2. Homepage Content
    hero_title = models.CharField(max_length=255, default="Drive with Confidence. Pass Your Test on First Attempt.")
    hero_subtitle = models.TextField(default="NTSA-accredited driving institution offering category A, B, and C curriculum with modern dual-pedal vehicles, certified professional instructors, and personalized schedules.")
    hero_image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    hero_cta_text = models.CharField(max_length=50, default="Enroll Now")
    hero_cta_link = models.CharField(max_length=100, default="/enroll/")

    about_section_tag = models.CharField(max_length=100, default="About Belings Driving School")
    about_section_title = models.CharField(max_length=255, default="Your Journey to Responsible, Confident Driving Starts Here")
    about_section_text = models.TextField(default="Established with a commitment to road safety and driving excellence, Belings Driving School has equipped thousands of Kenyan drivers with defensive motoring skills, sound road ethics, and technical proficiency.")

    courses_section_title = models.CharField(max_length=255, default="NTSA Approved Driving Courses")
    courses_section_desc = models.TextField(default="Comprehensive theoretical knowledge and hands-on practical hours tailored to equip you with defensive driving instincts.")

    why_choose_title = models.CharField(max_length=255, default="The Belings Advantage")
    why_choose_desc = models.TextField(default="We go beyond preparing you for a 15-minute test; we build confident, safety-conscious motorists equipped for Kenya's busy roadways.")

    cta_banner_badge = models.CharField(max_length=100, default="LIMITED SLOTS AVAILABLE")
    cta_banner_title = models.CharField(max_length=255, default="Ready to Get Behind the Wheel?")
    cta_banner_desc = models.TextField(default="Join thousands of successful drivers. Register today and enjoy affordable rates, installment options, and comprehensive NTSA test support.")
    cta_banner_btn_text = models.CharField(max_length=50, default="Start Online Enrollment")
    cta_banner_btn_link = models.CharField(max_length=100, default="/enroll/")

    # 3. Key Statistics
    stat_students = models.CharField(max_length=50, default="12,500+")
    stat_pass_rate = models.CharField(max_length=50, default="98.5%")
    stat_experience_years = models.CharField(max_length=50, default="12+")
    stat_certified_instructors = models.CharField(max_length=50, default="24+")

    # 4. Contact & Location
    phone = models.CharField(max_length=30, default="+254 700 123 456")
    phone_secondary = models.CharField(max_length=30, blank=True, default="+254 733 987 654")
    email = models.EmailField(default="info@belingsdriving.co.ke")
    address = models.CharField(max_length=255, default="Belings Towers, 3rd Floor, Moi Avenue / Commercial Street, Nairobi, Kenya")
    whatsapp_number = models.CharField(max_length=30, default="254700123456", help_text="Number in international format without + (e.g. 254700123456)")
    opening_hours = models.CharField(max_length=255, default="Mon - Fri: 7:00 AM - 6:30 PM | Sat: 8:00 AM - 4:00 PM | Sun: Closed")
    map_embed_url = models.TextField(blank=True, default="")

    # 5. Social Links
    facebook_url = models.URLField(blank=True, default="https://facebook.com/belingsdrivingschool")
    twitter_url = models.URLField(blank=True, default="https://twitter.com/belingsdriving")
    instagram_url = models.URLField(blank=True, default="https://instagram.com/belingsdrivingschool")
    linkedin_url = models.URLField(blank=True, default="https://linkedin.com/company/belingsdrivingschool")
    youtube_url = models.URLField(blank=True, default="https://youtube.com/@belingsdrivingschool")

    # 6. Accreditation & Footer
    ntsa_accreditation_note = models.CharField(max_length=255, default="Fully Accredited by the National Transport and Safety Authority (NTSA) - BDS/NTSA/2024/098")
    footer_about_text = models.TextField(default="Accredited driver training academy cultivating safe, skilled, and licensed drivers through modern pedagogy and defensive motoring skills.")
    copyright_text = models.CharField(max_length=150, default="Belings Driving School. All Rights Reserved.")

    # 7. SEO Configuration
    meta_title = models.CharField(max_length=150, default="Belings Driving School - NTSA Accredited Academy in Kenya")
    meta_description = models.TextField(default="Learn safe, defensive driving with certified instructors, modern dual-pedal fleet, and flexible schedules in Kenya.")
    og_image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    indexing_enabled = models.BooleanField(default=True, help_text="Allow search engines to index this website")

    # 8. Operational & System Settings
    currency_code = models.CharField(max_length=10, default="KES")
    currency_symbol = models.CharField(max_length=10, default="KES ")
    timezone = models.CharField(max_length=50, default="Africa/Nairobi")
    lesson_duration_minutes = models.PositiveIntegerField(default=60, help_text="Standard lesson duration in minutes")
    cancellation_window_hours = models.PositiveIntegerField(default=24, help_text="Hours notice required for lesson cancellation without charge")
    max_lessons_per_day = models.PositiveIntegerField(default=2, help_text="Maximum lessons a student can book in one day")
    mpesa_paybill = models.CharField(max_length=30, default="174379", blank=True)
    mpesa_account_ref = models.CharField(max_length=50, default="STUDENT_ID", blank=True)
    receipt_header_details = models.TextField(default="Belings Driving School Ltd\nP.O. Box 12345-00100, Nairobi\nTax PIN: P051234567Z\nNTSA Reg: BDS/NTSA/2024/098")
    sms_reminder_template = models.TextField(default="Dear {student_name}, your driving lesson for {course_name} is scheduled for tomorrow at {lesson_time}. Belings Driving School.")
    email_welcome_template = models.TextField(default="Welcome to Belings Driving School, {student_name}! Your enrollment for {course_name} has been received. Please report with your ID copy and 2 passport photos.")

    # 9. Maintenance Mode
    maintenance_mode = models.BooleanField(default=False, help_text="Show maintenance page to the public while allowing admins full access")
    maintenance_message = models.TextField(default="Belings Driving School website is currently undergoing scheduled maintenance. We will be back online shortly. For urgent inquiries call +254 700 123 456.")

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
        cache.delete(self.CACHE_KEY)

    @classmethod
    def load(cls):
        settings_obj = cache.get(cls.CACHE_KEY)
        if not settings_obj:
            settings_obj, created = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, settings_obj, timeout=3600)
        return settings_obj


class HeroSlide(models.Model):
    """Multiple orderable hero slider slides with on/off toggle."""
    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True)
    image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    cta_text = models.CharField(max_length=50, default="Enroll Now")
    cta_link = models.CharField(max_length=100, default="/enroll/")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Hero Slide"
        verbose_name_plural = "Hero Slides"

    def __str__(self):
        return self.title


class WhyChooseUsItem(models.Model):
    """Editable 'Why Choose Us' feature blocks on the homepage."""
    icon_class = models.CharField(max_length=60, default="bi-shield-check", help_text="Bootstrap Icon class (e.g. bi-shield-check, bi-car-front, bi-people)")
    title = models.CharField(max_length=120)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Why Choose Us Item"
        verbose_name_plural = "Why Choose Us Items"

    def __str__(self):
        return self.title


class PageContent(models.Model):
    """Editable static pages (About Us, FAQ, Terms of Service, Privacy Policy)."""
    PAGE_SLUGS = [
        ('about', 'About Us'),
        ('terms', 'Terms and Conditions'),
        ('privacy', 'Privacy Policy'),
        ('enrollment_guide', 'Enrollment & Admission Guide'),
    ]

    slug = models.CharField(max_length=50, unique=True, choices=PAGE_SLUGS)
    title = models.CharField(max_length=200)
    content = models.TextField(help_text="Page body content (HTML or structured text)")
    meta_description = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = "Page Content"
        verbose_name_plural = "Page Contents"

    def __str__(self):
        return self.title


class NavigationItem(models.Model):
    """Editable navigation menu items."""
    label = models.CharField(max_length=60)
    url = models.CharField(max_length=200, help_text="Relative (e.g. /about/) or external link")
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'label']
        verbose_name = "Navigation Menu Item"
        verbose_name_plural = "Navigation Menu Items"

    def __str__(self):
        return f"{self.label} -> {self.url}"


class Testimonial(models.Model):
    name = models.CharField(max_length=120)
    course_taken = models.CharField(max_length=150)
    rating = models.PositiveSmallIntegerField(default=5, choices=[(i, f"{i} Stars") for i in range(1, 6)])
    quote = models.TextField()
    avatar = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return f"{self.name} - {self.course_taken}"


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
    image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file])
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=200, blank=True, help_text="Accessibility alt text for screen readers")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.title
        super().save(*args, **kwargs)


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
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, help_text="Staff response notes or logs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} - {self.subject}"


class AuditLog(models.Model):
    """Audit log tracking who changed what setting or content and when."""
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_entries')
    action = models.CharField(max_length=100, help_text="e.g. UPDATE_BRANDING, EDIT_COURSE, CHANGE_MAINTENANCE")
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} - {self.action}"
