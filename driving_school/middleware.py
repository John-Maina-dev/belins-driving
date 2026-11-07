from django.shortcuts import render
from website.models import SiteSettings
from accounts.permissions import is_management_authorized

class MaintenanceModeMiddleware:
    """
    Shows a clean 'Under Maintenance / Back Soon' page to public visitors
    when maintenance_mode is enabled in SiteSettings, while allowing Super Admins
    and Admins to continue managing the system.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Always allow static files, media, and login/admin URLs
        exempt_prefixes = ['/static/', '/media/', '/admin/', '/manage/login/']
        if any(path.startswith(prefix) for prefix in exempt_prefixes):
            return self.get_response(request)

        try:
            settings_obj = SiteSettings.load()
            if settings_obj and settings_obj.maintenance_mode:
                # If logged-in user is an authorized admin/super-admin, allow access
                if request.user.is_authenticated and is_management_authorized(request.user):
                    return self.get_response(request)

                # Public visitor: show maintenance page with 503 Service Unavailable
                return render(
                    request,
                    'website/maintenance.html',
                    {'site_settings': settings_obj},
                    status=503
                )
        except Exception:
            # Fall back to normal request handling during migrations / setup
            pass

        return self.get_response(request)

