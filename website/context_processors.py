from .models import SiteSettings, NavigationItem

def site_settings(request):
    """
    Expose global site settings, navigation menu, and dynamic CSS styles
    to all public templates.
    """
    try:
        settings_obj = SiteSettings.load()
    except Exception:
        settings_obj = None

    try:
        nav_items = NavigationItem.objects.filter(is_visible=True).order_by('order', 'label')
    except Exception:
        nav_items = []

    return {
        'site_settings': settings_obj,
        'nav_items': nav_items,
    }
