from django import forms
from django.contrib.auth.models import User
from website.models import (
    SiteSettings, HeroSlide, WhyChooseUsItem, PageContent,
    NavigationItem, Testimonial, GalleryImage, GalleryCategory, FAQ, ContactMessage,
    EmailSettings, CustomSocialLink, HomeSection
)
from courses.models import Course, Branch, Vehicle
from courses.map_utils import normalize_map_embed_url
from instructors.models import Instructor
from accounts.models import UserProfile


class BrandingForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'school_name', 'tagline', 'logo_light', 'logo_dark', 'favicon',
            'brand_primary', 'brand_secondary', 'brand_accent',
            'font_heading', 'font_body'
        ]
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'logo_light': forms.FileInput(attrs={'class': 'form-control'}),
            'logo_dark': forms.FileInput(attrs={'class': 'form-control'}),
            'favicon': forms.FileInput(attrs={'class': 'form-control'}),
            'brand_primary': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'brand_secondary': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'brand_accent': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'font_heading': forms.Select(attrs={'class': 'form-select'}),
            'font_body': forms.Select(attrs={'class': 'form-select'}),
        }


class HomepageContentForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'hero_title', 'hero_subtitle', 'hero_image', 'hero_cta_text', 'hero_cta_link',
            'hero_overlay_enabled', 'hero_overlay_color', 'hero_overlay_opacity', 'hero_text_panel_enabled',
            'about_section_tag', 'about_section_title', 'about_section_text',
            'courses_section_title', 'courses_section_desc',
            'why_choose_title', 'why_choose_desc',
            'cta_banner_badge', 'cta_banner_title', 'cta_banner_desc',
            'cta_banner_btn_text', 'cta_banner_btn_link',
            'stat_students', 'stat_pass_rate', 'stat_experience_years', 'stat_certified_instructors',
            'home_gallery_count', 'home_gallery_show_tabs', 'home_gallery_featured_first', 'gallery_layout_size',
        ]
        widgets = {
            'hero_title': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hero_image': forms.FileInput(attrs={'class': 'form-control'}),
            'hero_cta_text': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_cta_link': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_overlay_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hero_overlay_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'hero_overlay_opacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 70}),
            'hero_text_panel_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'about_section_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'about_section_title': forms.TextInput(attrs={'class': 'form-control'}),
            'about_section_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'courses_section_title': forms.TextInput(attrs={'class': 'form-control'}),
            'courses_section_desc': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'why_choose_title': forms.TextInput(attrs={'class': 'form-control'}),
            'why_choose_desc': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cta_banner_badge': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_banner_title': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_banner_desc': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cta_banner_btn_text': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_banner_btn_link': forms.TextInput(attrs={'class': 'form-control'}),
            'stat_students': forms.TextInput(attrs={'class': 'form-control'}),
            'stat_pass_rate': forms.TextInput(attrs={'class': 'form-control'}),
            'stat_experience_years': forms.TextInput(attrs={'class': 'form-control'}),
            'stat_certified_instructors': forms.TextInput(attrs={'class': 'form-control'}),
            'home_gallery_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 24}),
            'home_gallery_show_tabs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'home_gallery_featured_first': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gallery_layout_size': forms.Select(attrs={'class': 'form-select'}),
        }


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = [
            'title', 'subtitle', 'image', 'cta_text', 'cta_link',
            'overlay_enabled', 'overlay_color', 'overlay_opacity', 'text_panel_enabled',
            'order', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'cta_text': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_link': forms.TextInput(attrs={'class': 'form-control'}),
            'overlay_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'overlay_color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'overlay_opacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 70}),
            'text_panel_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WhyChooseUsForm(forms.ModelForm):
    class Meta:
        model = WhyChooseUsItem
        fields = ['icon_class', 'title', 'description', 'order', 'is_active']
        widgets = {
            'icon_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-shield-check'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PageContentForm(forms.ModelForm):
    class Meta:
        model = PageContent
        fields = ['title', 'content', 'meta_description', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 12}),
            'meta_description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseForm(forms.ModelForm):
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all().order_by('order', 'name'),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Course
        fields = [
            'name', 'slug', 'license_category', 'category_display', 'duration', 'fee',
            'short_description', 'full_description', 'requirements', 'features',
            'practical_hours', 'theory_hours', 'icon_class', 'image', 'branches',
            'is_featured', 'is_active', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'license_category': forms.Select(attrs={'class': 'form-select'}),
            'category_display': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 4 Weeks'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '100'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'full_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'features': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'practical_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'theory_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'icon_class': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = [
            'full_name', 'title', 'license_categories', 'experience_years',
            'bio', 'photo', 'phone', 'email', 'ntsa_cert_number', 'branch',
            'is_featured', 'is_active', 'order'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'license_categories': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'ntsa_cert_number': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class GalleryCategoryForm(forms.ModelForm):
    class Meta:
        model = GalleryCategory
        fields = ['name', 'slug', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['title', 'category_obj', 'category', 'image', 'caption', 'alt_text', 'is_featured_home', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'category_obj': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_featured_home': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'course_taken', 'rating', 'quote', 'avatar', 'is_featured', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'course_taken': forms.TextInput(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'quote': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'category', 'order', 'is_active']
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NavigationItemForm(forms.ModelForm):
    class Meta:
        model = NavigationItem
        fields = ['label', 'url', 'order', 'is_visible', 'open_in_new_tab']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'url': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'open_in_new_tab': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContactSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'phone', 'phone_secondary', 'whatsapp_number', 'email', 'address',
            'opening_hours',
            'facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url',
            'footer_about_text', 'copyright_text', 'ntsa_accreditation_note',
        ]
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_secondary': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'opening_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'footer_about_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
            'ntsa_accreditation_note': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SocialLinksForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'facebook_url', 'facebook_enabled',
            'instagram_url', 'instagram_enabled',
            'twitter_url', 'twitter_enabled',
            'youtube_url', 'youtube_enabled',
            'tiktok_url', 'tiktok_enabled',
            'linkedin_url', 'linkedin_enabled',
            'whatsapp_number', 'whatsapp_enabled',
            'telegram_url', 'telegram_enabled',
        ]
        widgets = {
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'facebook_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/...'}),
            'instagram_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'twitter_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'youtube_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiktok_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://tiktok.com/@...'}),
            'tiktok_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/company/...'}),
            'linkedin_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '254712345678'}),
            'whatsapp_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'telegram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/...'}),
            'telegram_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomSocialLinkForm(forms.ModelForm):
    class Meta:
        model = CustomSocialLink
        fields = ['label', 'url', 'icon', 'order', 'is_active']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Threads', 'required': True}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...', 'required': True}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-globe'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


MAP_FIELD_WIDGETS = {
    'map_embed_url': forms.Textarea(attrs={
        'class': 'form-control font-monospace', 'rows': 3,
        'placeholder': 'https://www.google.com/maps?q=...&output=embed   (or paste the whole <iframe ...> code)',
        'data-map-input': 'embed',
    }),
    'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '-0.681700', 'data-map-input': 'lat'}),
    'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '34.766700', 'data-map-input': 'lng'}),
    'map_zoom': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 21, 'data-map-input': 'zoom'}),
}


class _MapFieldsCleaningMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zoom is optional in the form: an empty value falls back to the default of 16.
        if 'map_zoom' in self.fields:
            self.fields['map_zoom'].required = False

    def clean_map_zoom(self):
        zoom = self.cleaned_data.get('map_zoom')
        return 16 if zoom in (None, '') else zoom

    def clean_map_embed_url(self):
        # Accepts a plain URL or a pasted <iframe>; keeps only a validated Google Maps src.
        return normalize_map_embed_url(self.cleaned_data.get('map_embed_url'))


class BranchForm(_MapFieldsCleaningMixin, forms.ModelForm):
    class Meta:
        model = Branch
        fields = [
            'name', 'code', 'address', 'town', 'phone', 'email',
            'map_embed_url', 'latitude', 'longitude', 'map_zoom',
            'opening_hours', 'image', 'is_active', 'order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'data-map-input': 'address'}),
            'town': forms.TextInput(attrs={'class': 'form-control', 'data-map-input': 'town'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'opening_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            **MAP_FIELD_WIDGETS,
        }


class BranchMapForm(_MapFieldsCleaningMixin, forms.ModelForm):
    """Map-only branch form: what an Admin (not Super Admin) may change on a branch."""

    class Meta:
        model = Branch
        fields = ['map_embed_url', 'latitude', 'longitude', 'map_zoom']
        widgets = dict(MAP_FIELD_WIDGETS)



class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate_number', 'make_model', 'license_category', 'transmission', 'branch', 'is_active']
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'make_model': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'license_category': forms.TextInput(attrs={'class': 'form-control'}),
            'transmission': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmailSettingsForm(forms.ModelForm):
    smtp_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={'class': 'form-control', 'placeholder': 'Enter new SMTP password / App Password'}
        )
    )
    clear_password = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = EmailSettings
        fields = [
            'smtp_host', 'smtp_port', 'security_protocol', 'smtp_username',
            'default_from_name', 'default_from_email', 'reply_to_email', 'is_enabled'
        ]
        widgets = {
            'smtp_host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'smtp.gmail.com'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'security_protocol': forms.Select(attrs={'class': 'form-select'}),
            'smtp_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'school@example.com'}),
            'default_from_name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_from_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'reply_to_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        new_pw = self.cleaned_data.get('smtp_password')
        clear_pw = self.cleaned_data.get('clear_password')
        if clear_pw:
            obj.set_password('')
        elif new_pw:
            obj.set_password(new_pw)
        if commit:
            obj.save()
        return obj


class SEOForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['meta_title', 'meta_description', 'og_image', 'indexing_enabled']
        widgets = {
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'og_image': forms.FileInput(attrs={'class': 'form-control'}),
            'indexing_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'currency_code', 'currency_symbol', 'timezone',
            'lesson_duration_minutes', 'cancellation_window_hours', 'max_lessons_per_day',
            'session_timeout_minutes',
            'mpesa_paybill', 'mpesa_account_ref', 'receipt_header_details',
            'sms_reminder_template', 'email_welcome_template',
        ]
        widgets = {
            'currency_code': forms.TextInput(attrs={'class': 'form-control'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control'}),
            'lesson_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'cancellation_window_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_lessons_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'session_timeout_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'mpesa_paybill': forms.TextInput(attrs={'class': 'form-control'}),
            'mpesa_account_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'receipt_header_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sms_reminder_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email_welcome_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaintenanceModeForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['maintenance_mode', 'maintenance_message']
        widgets = {
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class UserManagementForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep existing password'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GalleryBatchUploadForm(forms.Form):
    """
    Multi-photo batch upload form using MultipleFileField (allow_multiple_selected=True).
    """
    from .fields import MultipleFileField
    images = MultipleFileField(required=False, label="Select Photos (Multiple Allowed)")
    category_obj = forms.ModelChoiceField(
        queryset=GalleryCategory.objects.all(),
        required=False,
        empty_label="-- Select Category --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_batch_category_obj'})
    )
    category = forms.ChoiceField(
        choices=GalleryImage.CATEGORY_CHOICES,
        initial='practical',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_batch_category'})
    )
    title_prefix = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional batch title prefix (defaults to filename)'})
    )
    caption = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional batch caption'})
    )
    is_featured_home = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_batch_featured'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category_obj'].queryset = GalleryCategory.objects.filter(is_active=True).order_by('order', 'name')


class StaffEnrollmentForm(forms.Form):
    """
    Staff Enrollment Form for Super Admin & Admin:
    Supports EITHER choosing an existing student (searchable) OR creating a new
    18+ student on the spot, then selecting branch, branch-filtered course,
    start date, editable total fee, optional discount with reason, and optional
    initial payment.
    """
    student_mode = forms.ChoiceField(
        choices=[('new', 'Create New Student'), ('existing', 'Select Existing Student')],
        initial='new',
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    existing_student = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="-- Search / Select Existing Student --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_existing_student'})
    )

    # New student fields
    first_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com'}))
    phone = forms.CharField(max_length=25, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0712 345 678'}))
    id_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport'}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    gender = forms.ChoiceField(choices=[('', '-- Select --'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False, widget=forms.Select(attrs={'class': 'form-select'}))

    # Course & Branch fields
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True).order_by('order', 'name'),
        required=True,
        empty_label="-- Select Branch --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_branch', 'required': True})
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True).order_by('order', 'name'),
        required=True,
        empty_label="-- Select Course --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_course', 'required': True})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    preferred_schedule = forms.ChoiceField(
        choices=[
            ('morning', 'Morning (8:00 AM - 11:00 AM)'),
            ('afternoon', 'Afternoon (1:00 PM - 4:00 PM)'),
            ('evening', 'Evening (4:30 PM - 7:00 PM)'),
            ('weekend', 'Weekend Intensive (Sat 8:00 AM - 4:00 PM)'),
        ],
        initial='morning',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Fee, Discount & First Payment fields
    total_fee = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '100', 'id': 'id_total_fee', 'placeholder': 'Defaults to course fee'})
    )
    discount_amount = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '100', 'id': 'id_discount_amount'})
    )
    discount_reason = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Required if discount > 0'})
    )
    initial_payment_amount = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '100', 'placeholder': '0.00'})
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('', '-- Select Method --'),
            ('MPESA', 'M-Pesa'),
            ('CASH', 'Cash'),
            ('BANK', 'Bank Transfer'),
            ('CARD', 'Debit / Credit Card'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_reference = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. QWE123RTY4 or Receipt #'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Staff remarks or notes'})
    )

    def __init__(self, *args, **kwargs):
        from datetime import date
        from students.models import Student
        super().__init__(*args, **kwargs)
        self.fields['existing_student'].queryset = Student.objects.all().order_by('first_name', 'last_name', '-created_at')
        self.fields['branch'].queryset = Branch.objects.filter(is_active=True).order_by('order', 'name')
        self.fields['course'].queryset = Course.objects.filter(is_active=True).order_by('order', 'name')
        today = date.today()
        try:
            max_dob = today.replace(year=today.year - 18)
        except ValueError:
            max_dob = today.replace(year=today.year - 18, month=2, day=28)
        self.fields['date_of_birth'].widget.attrs['max'] = max_dob.isoformat()
        if not self.initial.get('start_date'):
            self.initial['start_date'] = today.isoformat()

    def clean(self):
        from django.db.models import Q
        from django.utils import timezone
        from students.models import Student
        from students.validators import validate_age_18_plus

        cleaned = super().clean()
        mode = cleaned.get('student_mode') or 'new'
        existing_student = cleaned.get('existing_student')
        if existing_student and mode != 'existing':
            mode = 'existing'
            cleaned['student_mode'] = 'existing'

        branch = cleaned.get('branch')
        course = cleaned.get('course')

        if mode == 'existing':
            if not existing_student:
                self.add_error('existing_student', "Please select an existing student.")
            else:
                if not existing_student.date_of_birth:
                    self.add_error('existing_student', "Selected student does not have a valid date of birth on file.")
                else:
                    try:
                        validate_age_18_plus(existing_student.date_of_birth)
                    except forms.ValidationError as exc:
                        self.add_error('existing_student', exc.messages[0])
                cleaned['first_name'] = existing_student.first_name
                cleaned['last_name'] = existing_student.last_name
                cleaned['email'] = existing_student.email
                cleaned['phone'] = existing_student.phone
                cleaned['id_number'] = existing_student.id_number
                cleaned['date_of_birth'] = existing_student.date_of_birth
                cleaned['gender'] = existing_student.gender
        else:
            for req_field, label in [
                ('first_name', 'First name'),
                ('last_name', 'Last name'),
                ('email', 'Email address'),
                ('phone', 'Phone number'),
                ('id_number', 'ID / Passport number'),
                ('date_of_birth', 'Date of birth'),
            ]:
                if not cleaned.get(req_field):
                    self.add_error(req_field, f"{label} is required.")
            dob = cleaned.get('date_of_birth')
            if dob:
                try:
                    validate_age_18_plus(dob)
                except forms.ValidationError as exc:
                    self.add_error('date_of_birth', exc.messages[0])

        if branch and not branch.is_active:
            self.add_error('branch', "Selected branch is not active.")
        if branch and course:
            if course.branches.exists() and not course.branches.filter(pk=branch.pk).exists():
                self.add_error('course', f"The course '{course.name}' is not offered at {branch.name}.")

        discount = cleaned.get('discount_amount') or 0
        discount_reason = (cleaned.get('discount_reason') or '').strip()
        if discount > 0 and not discount_reason:
            self.add_error('discount_reason', "Please provide a reason for the discount.")

        init_pay = cleaned.get('initial_payment_amount') or 0
        pay_method = (cleaned.get('payment_method') or '').strip()
        if init_pay > 0 and not pay_method:
            self.add_error('payment_method', "Please select a payment method for the initial payment.")

        # Duplicate active enrollment check (same student + same course + still active)
        email = (cleaned.get('email') or '').strip()
        id_number = (cleaned.get('id_number') or '').strip()
        if course and (email or id_number or existing_student):
            active_statuses = ['PENDING_APPROVAL', 'pending', 'APPROVED', 'approved', 'enrolled']
            q = Q()
            if existing_student and existing_student.user_id:
                q |= Q(user_id=existing_student.user_id)
            if email:
                q |= Q(email__iexact=email)
            if id_number:
                q |= Q(id_number__iexact=id_number)
            if q and Student.objects.filter(q, course=course, status__in=active_statuses).exists():
                self.add_error('course', "This student already has an active enrollment in this course (already enrolled).")

        if not cleaned.get('start_date'):
            cleaned['start_date'] = timezone.localdate()
        if cleaned.get('total_fee') is None and course:
            cleaned['total_fee'] = course.fee

        return cleaned

