from django.contrib import admin
from django.utils.html import format_html
from .models import SiteSettings, Testimonial, GalleryImage, FAQ, ContactMessage

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("School Branding & Identity", {
            "fields": ("school_name", "tagline", "logo", "ntsa_accreditation_note"),
            "description": "Customize the brand name, tagline, NTSA registration note, and upload school logo."
        }),
        ("Hero Section (Homepage)", {
            "fields": ("hero_title", "hero_subtitle", "hero_image", "hero_cta_text", "hero_cta_link"),
            "description": "Main banner headline and call to action shown to visitors."
        }),
        ("Contact & Location Details", {
            "fields": ("phone", "phone_secondary", "email", "address", "whatsapp_number", "opening_hours", "map_embed_url"),
            "description": "Shown on topbar, contact page, and footer."
        }),
        ("About Us Details", {
            "fields": ("about_story", "mission", "vision"),
        }),
        ("Homepage Counter Statistics", {
            "fields": ("stat_students", "stat_pass_rate", "stat_experience_years", "stat_certified_instructors"),
        }),
        ("Social Media Profiles", {
            "fields": ("facebook_url", "twitter_url", "instagram_url", "linkedin_url", "youtube_url"),
        }),
    )

    def has_add_permission(self, request):
        # Enforce singleton
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_taken', 'rating_stars', 'is_featured', 'is_active', 'order', 'created_at')
    list_filter = ('rating', 'is_featured', 'is_active')
    search_fields = ('name', 'course_taken', 'quote')
    list_editable = ('is_featured', 'is_active', 'order')

    def rating_stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
    rating_stars.short_description = "Rating"


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'thumbnail', 'order', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'caption')
    list_editable = ('order', 'is_active')

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="40" style="object-fit:cover; border-radius:4px;" />', obj.image.url)
        return "No Image"
    thumbnail.short_description = "Preview"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    list_editable = ('is_resolved',)
    readonly_fields = ('name', 'email', 'phone', 'subject', 'message', 'created_at')
