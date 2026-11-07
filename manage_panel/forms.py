from django import forms
from django.contrib.auth.models import User
from website.models import (
    SiteSettings, HeroSlide, WhyChooseUsItem, PageContent,
    NavigationItem, Testimonial, GalleryImage, FAQ, ContactMessage
)
from courses.models import Course
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
            'about_section_tag', 'about_section_title', 'about_section_text',
            'courses_section_title', 'courses_section_desc',
            'why_choose_title', 'why_choose_desc',
            'cta_banner_badge', 'cta_banner_title', 'cta_banner_desc',
            'cta_banner_btn_text', 'cta_banner_btn_link',
            'stat_students', 'stat_pass_rate', 'stat_experience_years', 'stat_certified_instructors',
        ]
        widgets = {
            'hero_title': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hero_image': forms.FileInput(attrs={'class': 'form-control'}),
            'hero_cta_text': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_cta_link': forms.TextInput(attrs={'class': 'form-control'}),
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
        }


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = ['title', 'subtitle', 'image', 'cta_text', 'cta_link', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'cta_text': forms.TextInput(attrs={'class': 'form-control'}),
            'cta_link': forms.TextInput(attrs={'class': 'form-control'}),
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
    class Meta:
        model = Course
        fields = [
            'name', 'slug', 'license_category', 'category_display', 'duration', 'fee',
            'short_description', 'full_description', 'requirements', 'features',
            'practical_hours', 'theory_hours', 'icon_class', 'image',
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
            'bio', 'photo', 'phone', 'email', 'ntsa_cert_number',
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
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['title', 'category', 'image', 'caption', 'alt_text', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
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
            'opening_hours', 'map_embed_url',
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
            'map_embed_url': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'footer_about_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'copyright_text': forms.TextInput(attrs={'class': 'form-control'}),
            'ntsa_accreditation_note': forms.TextInput(attrs={'class': 'form-control'}),
        }


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

