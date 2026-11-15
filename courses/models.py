from decimal import Decimal
from urllib.parse import parse_qs, quote_plus, urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from website.models import safe_upload_path, validate_image_file
from .map_utils import MAP_HELP_TEXT, UNVERIFIED_NOTE, DEFAULT_MAIN_BRANCH_EMBED, normalize_map_embed_url, is_safe_map_url

class Branch(models.Model):
    name = models.CharField(max_length=150, help_text="e.g. Main Campus - Kisii")
    code = models.CharField(max_length=30, unique=True, help_text="e.g. KSI-MAIN")
    address = models.CharField(max_length=255, blank=True, default="", help_text="Street address / building")
    town = models.CharField(max_length=100, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    map_embed_url = models.TextField(
        blank=True, default="",
        help_text=f"{MAP_HELP_TEXT} Leave empty to build the map from latitude/longitude or the address. {UNVERIFIED_NOTE}",
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(Decimal('-90')), MaxValueValidator(Decimal('90'))],
        help_text="Optional, e.g. -0.681700 (used when no embed link is set)",
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(Decimal('-180')), MaxValueValidator(Decimal('180'))],
        help_text="Optional, e.g. 34.766700",
    )
    map_zoom = models.PositiveSmallIntegerField(
        default=16, validators=[MinValueValidator(1), MaxValueValidator(21)],
        help_text="Map zoom level from 1 (world) to 21 (building). Default 16.",
    )
    opening_hours = models.CharField(max_length=200, blank=True, default="Mon - Fri: 7:00 AM - 6:30 PM | Sat: 8:00 AM - 4:00 PM")
    image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True, help_text="Optional campus branch photo")
    is_active = models.BooleanField(default=True, help_text="Open for admissions and lessons")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.name} ({self.town})"

    # ------------------------------------------------------------------
    # Map helpers (all output is built from validated pieces only)
    # ------------------------------------------------------------------
    def clean(self):
        super().clean()
        errors = {}
        try:
            self.map_embed_url = normalize_map_embed_url(self.map_embed_url)
        except ValidationError as exc:
            errors['map_embed_url'] = exc.messages
        if (self.latitude is None) != (self.longitude is None):
            errors['latitude' if self.latitude is None else 'longitude'] = (
                "Enter both latitude and longitude, or leave both empty."
            )
        if errors:
            raise ValidationError(errors)

    @property
    def _safe_embed_url(self):
        """Stored embed URL, re-validated at render time (defence in depth)."""
        value = (self.map_embed_url or '').strip()
        return value if value and is_safe_map_url(value) else ''

    @property
    def _has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def _coordinate_text(self):
        return f"{Decimal(str(self.latitude)):.6f},{Decimal(str(self.longitude)):.6f}"

    @property
    def _address_query(self):
        address = (self.address or '').strip()
        if not address:
            return ''
        town = (self.town or '').strip()
        if town and town.lower() not in address.lower():
            address = f"{address}, {town}"
        return address

    @property
    def _zoom(self):
        return self.map_zoom if self.map_zoom else 16

    @property
    def map_src(self):
        """Iframe source: embed URL, else lat/lng, else address, else '' (no map)."""
        embed = self._safe_embed_url
        if embed:
            return embed
        if self._has_coordinates:
            return f"https://www.google.com/maps?q={self._coordinate_text}&z={self._zoom}&output=embed"
        query = self._address_query
        if query:
            return f"https://www.google.com/maps?q={quote_plus(query)}&z={self._zoom}&output=embed"
        return ''

    @property
    def has_map(self):
        return bool(self.map_src)

    @property
    def _destination_text(self):
        """Best destination for links: coordinates, address, or the q= of the embed."""
        if self._has_coordinates:
            return self._coordinate_text
        query = self._address_query
        if query:
            return query
        embed = self._safe_embed_url
        if embed:
            q = parse_qs(urlsplit(embed).query).get('q')
            if q and q[0].strip():
                return q[0].strip()
        return ''

    @property
    def directions_url(self):
        destination = self._destination_text
        if not destination:
            return ''
        return f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(destination)}"

    @property
    def maps_open_url(self):
        """'Open in Google Maps' link (search page for the same place)."""
        destination = self._destination_text
        if destination:
            return f"https://www.google.com/maps/search/?api=1&query={quote_plus(destination)}"
        return self._safe_embed_url

    @property
    def map_is_unverified_default(self):
        return (self.map_embed_url or '').strip() == DEFAULT_MAIN_BRANCH_EMBED


class Vehicle(models.Model):
    TRANSMISSION_CHOICES = [
        ('MANUAL', 'Manual Transmission'),
        ('AUTOMATIC', 'Automatic Transmission'),
    ]
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available for Lessons'),
        ('IN_USE', 'Currently in Session'),
        ('MAINTENANCE', 'Service / Maintenance'),
        ('INACTIVE', 'Decommissioned'),
    ]

    plate_number = models.CharField(max_length=20, unique=True, help_text="e.g. KDA 123X")
    make_model = models.CharField(max_length=100, help_text="e.g. Toyota Vitz (Dual-Pedal)")
    transmission = models.CharField(max_length=15, choices=TRANSMISSION_CHOICES, default='MANUAL')
    license_category = models.CharField(max_length=10, default='B')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='vehicles')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['plate_number']
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    @property
    def registration_number(self):
        return self.plate_number

    def __str__(self):
        return f"{self.plate_number} - {self.make_model} ({self.get_transmission_display()})"


class Course(models.Model):
    CATEGORY_CHOICES = [
        ('A', 'Category A - Motorcycle (A1, A2, A3)'),
        ('B', 'Category B - Light Vehicle (Manual & Automatic)'),
        ('C', 'Category C - Commercial & Medium Trucks'),
        ('D', 'Category D - Public Service Vehicles (PSV)'),
        ('E', 'Category E - Heavy Articulated Vehicles & Trailers'),
        ('R', 'Refresher & Defensive Driving Courses'),
    ]

    name = models.CharField(max_length=200, help_text="e.g. Category B Light Vehicle (Manual)")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    license_category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='B')
    category_display = models.CharField(max_length=100, blank=True, help_text="Custom display for category badge")
    branches = models.ManyToManyField(Branch, related_name='courses', blank=True, help_text="Branches offering this course")
    duration = models.CharField(max_length=50, default="4 Weeks", help_text="e.g. 4 Weeks / 30 Hours")
    fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fee in KES")
    short_description = models.TextField(help_text="Brief summary shown on course cards")
    full_description = models.TextField(blank=True, help_text="In-depth syllabus, topics, and overview")
    requirements = models.TextField(
        default="• Minimum 18 years of age\n• Copy of National ID / Passport\n• 2 Passport photos\n• Medical fitness declaration",
        help_text="Bullet points or requirements"
    )
    practical_hours = models.PositiveIntegerField(default=20, help_text="Practical driving lessons hours")
    theory_hours = models.PositiveIntegerField(default=15, help_text="Classroom theory & road safety hours")
    features = models.TextField(
        default="• NTSA Curriculum aligned\n• Free Interim Driving License assistance\n• First Aid & Basic Mechanics module\n• Flexible morning, afternoon & weekend batches",
        help_text="Highlights included with this course"
    )
    icon_class = models.CharField(max_length=50, default="bi-car-front", help_text="Bootstrap Icons class name")
    image = models.ImageField(upload_to=safe_upload_path, validators=[validate_image_file], blank=True, null=True, help_text="Optional cover image")
    is_featured = models.BooleanField(default=True, help_text="Feature on homepage")
    is_active = models.BooleanField(default=True, help_text="Show on website")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.category_display:
            self.category_display = self.get_license_category_display()
        super().save(*args, **kwargs)

    @property
    def code(self):
        return self.license_category

    def __str__(self):
        return f"{self.name} - KES {self.fee:,.0f}"

    def get_absolute_url(self):
        return reverse('website:course_detail', kwargs={'slug': self.slug})

