import os
import uuid
import re
from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache

def safe_upload_path(instance, filename):
    """Generate safe, randomized UUID filename to prevent arbitrary file upload vulnerabilities."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.ico', '.gif']:
        ext = '.jpg'
    return f"uploads/{uuid.uuid4().hex}{ext}"

def validate_image_file(file):
    """Validate image file format and integrity using Pillow (max 8 MB)."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp', '.ico', '.gif']:
        raise ValidationError("Unsupported format. Allowed formats: JPG, PNG, WEBP, ICO, GIF.")
    from .image_utils import validate_uploaded_image_strict
    validate_uploaded_image_strict(file)

def validate_hex_color(value):
    """Validate 3 or 6 digit hex color string (e.g. #020381)."""
    if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
        raise ValidationError("Invalid hex color code. Must be in format #RRGGBB or #RGB.")

def validate_kenyan_phone(value):
    """Validate Kenyan phone number format."""
    clean = re.sub(r'[\s\-]', '', value)
    if not re.match(r'^(?:\+254|0)[17]\d{8}$', clean):
        raise ValidationError("Enter a valid Kenyan phone number (e.g. 0712 345 678 or +254 700 123 456).")


def hex_to_rgba(hex_color, opacity_percent):
    """Convert hex color and 0-70% opacity to CSS rgba() string."""
    hex_str = (hex_color or '#000000').strip().lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c * 2 for c in hex_str])
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
    except Exception:
        r, g, b = 0, 0, 0
    alpha = max(0, min(70, int(opacity_percent or 0))) / 100.0
    return f"rgba({r}, {g}, {b}, {alpha:.2f})"


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
    school_name = models.CharField(max_length=150, default="Belings Driving School", blank=True)
    tagline = models.CharField(max_length=255, blank=True, default="")
    logo_light = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True, help_text="Logo for dark backgrounds")
    logo_dark = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True, help_text="Logo for light backgrounds")
    favicon = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    brand_primary = models.CharField(max_length=10, default="#020381", validators=[validate_hex_color], help_text="Primary Brand Navy")
    brand_secondary = models.CharField(max_length=10, default="#e9a825", validators=[validate_hex_color], help_text="Golden Accent / Buttons")
    brand_accent = models.CharField(max_length=10, default="#25D366", validators=[validate_hex_color], help_text="WhatsApp / Success Green")
    font_heading = models.CharField(max_length=100, choices=FONT_HEADING_CHOICES, default="'Roboto Slab', serif")
    font_body = models.CharField(max_length=100, choices=FONT_BODY_CHOICES, default="'Inter', sans-serif")

    # 2. Homepage Content
    hero_title = models.CharField(max_length=255, blank=True, default="")
    hero_subtitle = models.TextField(blank=True, default="")
    hero_image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    hero_overlay_enabled = models.BooleanField(default=False, help_text="Enable dark color overlay on hero image")
    hero_overlay_color = models.CharField(max_length=20, default="#000000", help_text="Overlay color in hex (default #000000)")
    hero_overlay_opacity = models.PositiveSmallIntegerField(default=0, help_text="Overlay opacity (0 to 70%)")
    hero_text_panel_enabled = models.BooleanField(default=False, help_text="Show semi-transparent panel behind hero text")
    hero_cta_text = models.CharField(max_length=50, blank=True, default="Enroll Now")
    hero_cta_link = models.CharField(max_length=100, blank=True, default="/enroll/")

    about_section_tag = models.CharField(max_length=100, blank=True, default="")
    about_section_title = models.CharField(max_length=255, blank=True, default="")
    about_section_text = models.TextField(blank=True, default="")

    courses_section_title = models.CharField(max_length=255, blank=True, default="")
    courses_section_desc = models.TextField(blank=True, default="")

    why_choose_title = models.CharField(max_length=255, blank=True, default="")
    why_choose_desc = models.TextField(blank=True, default="")

    cta_banner_badge = models.CharField(max_length=100, blank=True, default="")
    cta_banner_title = models.CharField(max_length=255, blank=True, default="")
    cta_banner_desc = models.TextField(blank=True, default="")
    cta_banner_btn_text = models.CharField(max_length=50, blank=True, default="Start Online Enrollment")
    cta_banner_btn_link = models.CharField(max_length=100, blank=True, default="/enroll/")

    # 3. Key Statistics
    stat_students = models.CharField(max_length=50, blank=True, default="")
    stat_pass_rate = models.CharField(max_length=50, blank=True, default="")
    stat_experience_years = models.CharField(max_length=50, blank=True, default="")
    stat_certified_instructors = models.CharField(max_length=50, blank=True, default="")

    # 4. Contact & Location
    phone = models.CharField(max_length=30, blank=True, default="")
    phone_secondary = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    whatsapp_number = models.CharField(max_length=30, blank=True, default="", help_text="Number in international format without + (e.g. 254700123456)")
    whatsapp_enabled = models.BooleanField(default=True)
    opening_hours = models.CharField(max_length=255, blank=True, default="")

    # 5. Social Links
    facebook_url = models.URLField(blank=True, default="")
    facebook_enabled = models.BooleanField(default=True)
    twitter_url = models.URLField(blank=True, default="")
    twitter_enabled = models.BooleanField(default=True)
    instagram_url = models.URLField(blank=True, default="")
    instagram_enabled = models.BooleanField(default=True)
    linkedin_url = models.URLField(blank=True, default="")
    linkedin_enabled = models.BooleanField(default=True)
    youtube_url = models.URLField(blank=True, default="")
    youtube_enabled = models.BooleanField(default=True)
    tiktok_url = models.URLField(blank=True, default="")
    tiktok_enabled = models.BooleanField(default=True)
    telegram_url = models.URLField(blank=True, default="")
    telegram_enabled = models.BooleanField(default=True)

    # 6. Accreditation & Footer
    ntsa_accreditation_note = models.CharField(max_length=255, blank=True, default="")
    footer_about_text = models.TextField(blank=True, default="")
    copyright_text = models.CharField(max_length=150, blank=True, default="")

    # 7. SEO Configuration
    meta_title = models.CharField(max_length=150, blank=True, default="Belings Driving School")
    meta_description = models.TextField(blank=True, default="")
    og_image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    indexing_enabled = models.BooleanField(default=True, help_text="Allow search engines to index this website")

    # 8. Operational & System Settings
    currency_code = models.CharField(max_length=10, default="KES")
    currency_symbol = models.CharField(max_length=10, default="KES ")
    timezone = models.CharField(max_length=50, default="Africa/Nairobi")
    session_timeout_minutes = models.PositiveIntegerField(default=15, help_text="Auto logout timeout in minutes after inactivity (default 15)")
    home_gallery_count = models.PositiveIntegerField(default=6, help_text="Number of photos shown in home gallery")
    home_gallery_show_tabs = models.BooleanField(default=True, help_text="Show category filter tabs on the home gallery")
    home_gallery_featured_first = models.BooleanField(default=True, help_text="Show featured gallery photos first")
    gallery_layout_size = models.CharField(
        max_length=10,
        choices=[('LARGE', 'Large (3 Columns, Big Cards)'), ('MEDIUM', 'Medium (4 Columns, Compact)')],
        default='LARGE',
        help_text="Gallery card layout size on public pages"
    )
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
        existing = SiteSettings.objects.exclude(pk=self.pk).first()
        if existing:
            raise ValidationError("There can only be one SiteSettings instance.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create(pk=1)
        return obj

    @property
    def overlay_rgba(self):
        return hex_to_rgba(self.hero_overlay_color, self.hero_overlay_opacity)

    @property
    def hero_overlay_rgba(self):
        return self.overlay_rgba

    @property
    def cta_banner_tag(self):
        return self.cta_banner_badge

    @property
    def cta_banner_subtitle(self):
        return self.cta_banner_desc


class HeroSlide(models.Model):
    """Multiple orderable hero slider slides with on/off toggle and custom overlay."""
    title = models.CharField(max_length=200)
    subtitle = models.TextField(blank=True)
    image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True)
    image_large = models.ImageField(upload_to=safe_upload_path, blank=True, null=True)
    overlay_enabled = models.BooleanField(default=False, help_text="Enable dark tint overlay on slide")
    overlay_color = models.CharField(max_length=20, default="#000000", help_text="Overlay color hex (e.g. #000000)")
    overlay_opacity = models.PositiveSmallIntegerField(default=0, help_text="Overlay opacity (0 to 70%)")
    text_panel_enabled = models.BooleanField(default=False, help_text="Display text inside a semi-transparent panel for readability")
    cta_text = models.CharField(max_length=50, blank=True, default="Enroll Now")
    cta_link = models.CharField(max_length=100, blank=True, default="/enroll/")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Hero Slide"
        verbose_name_plural = "Hero Slides"

    def __str__(self):
        return self.title

    @property
    def large_url(self):
        if self.image_large:
            return self.image_large.url
        return self.image.url if self.image else ''

    @property
    def overlay_rgba(self):
        return hex_to_rgba(self.overlay_color, self.overlay_opacity)

    def save(self, *args, **kwargs):
        if self.image and not getattr(self.image, '_committed', True):
            try:
                from .image_utils import generate_image_variants
                variants = generate_image_variants(self.image)
                large_file = variants['large_file']
                self.image_large.save(large_file.name, large_file, save=False)
            except Exception:
                pass
        super().save(*args, **kwargs)


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


class GalleryCategory(models.Model):
    name = models.CharField(max_length=100, help_text="e.g. Practical, Theory, Fleet, Classroom, Events")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Gallery Category"
        verbose_name_plural = "Gallery Categories"

    DEFAULT_CATEGORIES = [
        ('Practical', 'practical', 1),
        ('Theory', 'theory', 2),
        ('Classroom', 'classroom', 3),
        ('Fleet', 'fleet', 4),
        ('Events', 'events', 5),
    ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def ensure_defaults(cls):
        from django.db import IntegrityError
        for name, slug, order in cls.DEFAULT_CATEGORIES:
            try:
                cls.objects.get_or_create(
                    slug=slug,
                    defaults={'name': name, 'order': order, 'is_active': True}
                )
            except IntegrityError:
                pass
        return cls.objects.all().order_by('order', 'name')


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
    category_obj = models.ForeignKey(GalleryCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='images')
    image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file])
    image_grid = models.ImageField(upload_to=safe_upload_path, blank=True, null=True)
    image_large = models.ImageField(upload_to=safe_upload_path, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=200, blank=True, help_text="Accessibility alt text for screen readers")
    is_featured_home = models.BooleanField(default=True, help_text="Show in homepage gallery section")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"

    @property
    def is_featured(self):
        return self.is_featured_home

    @property
    def grid_url(self):
        if self.image_grid:
            return self.image_grid.url
        return self.image.url if self.image else ''

    @property
    def large_url(self):
        if self.image_large:
            return self.image_large.url
        return self.image.url if self.image else ''

    @property
    def category_slug(self):
        if self.category_obj and self.category_obj.slug:
            return self.category_obj.slug
        return self.category or 'practical'

    @property
    def category_label(self):
        if self.category_obj and self.category_obj.name:
            return self.category_obj.name
        return self.get_category_display()

    def __str__(self):
        return f"{self.title} ({self.category_label})"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.title
        if self.image and (not self.image_grid or not getattr(self.image, '_committed', True)):
            try:
                from .image_utils import generate_image_variants
                variants = generate_image_variants(self.image)
                grid_file = variants['grid_file']
                large_file = variants['large_file']
                self.image_grid.save(grid_file.name, grid_file, save=False)
                self.image_large.save(large_file.name, large_file, save=False)
            except Exception:
                pass
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


class EmailSettings(models.Model):
    is_enabled = models.BooleanField(default=False, help_text="Enable custom SMTP email sending")
    smtp_host = models.CharField(max_length=255, blank=True, default='smtp.gmail.com')
    smtp_port = models.PositiveIntegerField(default=587)
    security_protocol = models.CharField(
        max_length=10,
        choices=[('TLS', 'STARTTLS (Port 587)'), ('SSL', 'SSL/TLS (Port 465)'), ('NONE', 'None (Port 25)')],
        default='TLS'
    )
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password_encrypted = models.TextField(blank=True)
    default_from_name = models.CharField(max_length=150, default='Belings Driving School')
    default_from_email = models.EmailField(default='info@belingsdriving.co.ke')
    reply_to_email = models.EmailField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Email SMTP Settings"
        verbose_name_plural = "Email SMTP Settings"

    @property
    def security(self):
        return self.security_protocol

    @property
    def reply_to(self):
        return self.reply_to_email

    @property
    def encrypted_password(self):
        return self.smtp_password_encrypted

    @property
    def has_password(self):
        return bool(self.smtp_password_encrypted and self.smtp_password_encrypted.strip())

    def set_password(self, raw_password):
        from .encryption import encrypt_value
        self.smtp_password_encrypted = encrypt_value(raw_password) if raw_password else ''

    def get_password(self):
        from .encryption import decrypt_value
        return decrypt_value(self.smtp_password_encrypted)

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create(pk=1)
        return obj


class EmailLog(models.Model):
    sender = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_emails')
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=[('SENT', 'Sent'), ('FAILED', 'Failed')], default='SENT')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"

    @property
    def sent_at(self):
        return self.created_at

    def __str__(self):
        return f"To {self.recipient}: {self.subject} ({self.status})"


class CustomSocialLink(models.Model):
    label = models.CharField(max_length=60, help_text="e.g. TikTok, Telegram, Discord")
    url = models.URLField()
    icon = models.CharField(max_length=50, blank=True, default="bi-link-45deg", help_text="Bootstrap Icons class (e.g. bi-tiktok, bi-telegram, bi-whatsapp)")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'label']
        verbose_name = "Custom Social Link"
        verbose_name_plural = "Custom Social Links"

    @property
    def icon_class(self):
        return self.icon

    def __str__(self):
        return self.label


class HomeSectionManager(models.Manager):
    def ensure_defaults(self):
        return self.model.ensure_defaults()


class HomeSection(models.Model):
    DEFAULT_SECTIONS = [
        ('hero', 'Hero Slider / Banner', 1),
        ('stats', 'Statistics Counters', 2),
        ('about', 'About Us & Mission', 3),
        ('courses', 'Featured Courses', 4),
        ('branches', 'Campus Branches & Locations', 5),
        ('gallery', 'Photo Gallery Showcase', 6),
        ('why_choose_us', 'Why Choose Belings', 7),
        ('testimonials', 'Student Testimonials', 8),
        ('instructors', 'Instructors Preview', 9),
        ('faqs', 'Frequently Asked Questions', 10),
        ('cta', 'Enrollment Call to Action', 11),
        ('contact', 'Contact & Location Summary', 12),
    ]

    SECTION_CHOICES = [
        ('hero', 'Hero Slider / Banner'),
        ('stats', 'Statistics Counters'),
        ('about', 'About Us & Mission'),
        ('courses', 'Featured Courses'),
        ('branches', 'Campus Branches & Locations'),
        ('gallery', 'Photo Gallery Showcase'),
        ('why_choose_us', 'Why Choose Belings'),
        ('why_us', 'Why Choose Belings'),
        ('testimonials', 'Student Testimonials'),
        ('instructors', 'Instructors Preview'),
        ('faqs', 'Frequently Asked Questions'),
        ('cta', 'Enrollment Call to Action'),
        ('contact', 'Contact & Location Summary'),
    ]

    section_key = models.CharField(max_length=50, unique=True, choices=SECTION_CHOICES)
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_enabled = models.BooleanField(default=True)

    objects = HomeSectionManager()

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Homepage Section"
        verbose_name_plural = "Homepage Sections"

    @classmethod
    def ensure_defaults(cls):
        """
        Idempotently create the 12 standard homepage section rows if missing.
        Uses get_or_create so it is safe under concurrent requests, never
        overwrites an admin's existing order or visibility settings, and never
        creates any marketing content.
        """
        from django.db import IntegrityError
        # Normalize any legacy 'why_us' key to 'why_choose_us' if 'why_choose_us' does not exist yet
        if cls.objects.filter(section_key='why_us').exists() and not cls.objects.filter(section_key='why_choose_us').exists():
            cls.objects.filter(section_key='why_us').update(section_key='why_choose_us')

        for key, title, default_order in cls.DEFAULT_SECTIONS:
            try:
                cls.objects.get_or_create(
                    section_key=key,
                    defaults={
                        'title': title,
                        'order': default_order,
                        'is_enabled': True,
                    }
                )
            except IntegrityError:
                pass
        return cls.objects.all().order_by('order', 'id')

    def __str__(self):
        return f"{self.title} ({'Visible' if self.is_enabled else 'Hidden'})"
