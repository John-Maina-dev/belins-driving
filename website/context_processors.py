from .models import SiteSettings, NavigationItem, CustomSocialLink
from courses.models import Branch
from accounts.models import UserProfile
from students.models import Student, LessonBooking


def site_settings(request):
    """
    Expose global site settings, navigation menu, active social links,
    active branches, session timeout, and admin badge metrics.
    """
    try:
        settings_obj = SiteSettings.objects.first() or SiteSettings(pk=1)
    except Exception:
        settings_obj = None

    try:
        nav_items = NavigationItem.objects.filter(is_visible=True).order_by('order', 'label')
    except Exception:
        nav_items = []

    active_social_links = []
    if settings_obj:
        social_Configs = [
            ('Facebook', settings_obj.facebook_url, getattr(settings_obj, 'facebook_enabled', True), 'bi-facebook'),
            ('Instagram', settings_obj.instagram_url, getattr(settings_obj, 'instagram_enabled', True), 'bi-instagram'),
            ('X (Twitter)', settings_obj.twitter_url, getattr(settings_obj, 'twitter_enabled', True), 'bi-twitter-x'),
            ('YouTube', settings_obj.youtube_url, getattr(settings_obj, 'youtube_enabled', True), 'bi-youtube'),
            ('TikTok', getattr(settings_obj, 'tiktok_url', ''), getattr(settings_obj, 'tiktok_enabled', True), 'bi-tiktok'),
            ('LinkedIn', settings_obj.linkedin_url, getattr(settings_obj, 'linkedin_enabled', True), 'bi-linkedin'),
            ('Telegram', getattr(settings_obj, 'telegram_url', ''), getattr(settings_obj, 'telegram_enabled', True), 'bi-telegram'),
        ]
        for label, url, enabled, icon in social_Configs:
            if enabled and url and url.strip():
                active_social_links.append({
                    'label': label,
                    'url': url.strip(),
                    'icon': icon,
                })
        if getattr(settings_obj, 'whatsapp_enabled', True) and settings_obj.whatsapp_number and settings_obj.whatsapp_number.strip():
            wa_num = settings_obj.whatsapp_number.strip().lstrip('+')
            active_social_links.append({
                'label': 'WhatsApp',
                'url': f"https://wa.me/{wa_num}",
                'icon': 'bi-whatsapp',
            })

    try:
        custom_social_links = list(CustomSocialLink.objects.filter(is_active=True).order_by('order', 'label'))
    except Exception:
        custom_social_links = []

    try:
        active_branches = list(Branch.objects.filter(is_active=True).order_by('order', 'name'))
    except Exception:
        active_branches = []

    timeout_minutes = 15
    if settings_obj and getattr(settings_obj, 'session_timeout_minutes', None):
        timeout_minutes = max(1, int(settings_obj.session_timeout_minutes))
    session_timeout_seconds = timeout_minutes * 60

    pending_registrations_count = 0
    pending_enrollments_count = 0
    pending_lessons_count = 0
    if request.user.is_authenticated and (
        request.user.is_superuser
        or (hasattr(request.user, 'profile') and request.user.profile.is_management_authorized)
    ):
        try:
            pending_registrations_count = UserProfile.objects.filter(approval_status='PENDING').count()
            pending_enrollments_count = Student.objects.filter(status__in=['pending', 'PENDING_APPROVAL']).count()
            pending_lessons_count = LessonBooking.objects.filter(status='COMPLETED').count()
        except Exception:
            pass

    return {
        'site_settings': settings_obj,
        'nav_items': nav_items,
        'active_social_links': active_social_links,
        'custom_social_links': custom_social_links,
        'active_branches': active_branches,
        'session_timeout_seconds': session_timeout_seconds,
        'pending_registrations_count': pending_registrations_count,
        'pending_enrollments_count': pending_enrollments_count,
        'pending_lessons_count': pending_lessons_count,
    }
