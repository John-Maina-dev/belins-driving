from django.db import models
from django.urls import reverse
from django.utils.text import slugify

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
    image = models.ImageField(upload_to='courses/', blank=True, null=True, help_text="Optional cover image")
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

    def __str__(self):
        return f"{self.name} - KES {self.fee:,.0f}"

    def get_absolute_url(self):
        return reverse('website:course_detail', kwargs={'slug': self.slug})
