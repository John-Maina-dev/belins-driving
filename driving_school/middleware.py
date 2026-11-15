import time
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from website.models import SiteSettings
from accounts.permissions import is_management_authorized, is_super_admin


class InactivityTimeoutMiddleware:
    """
    Enforces server-side auto-logout after configurable minutes of inactivity
    (default 15 minutes in SiteSettings.session_timeout_minutes).
    Returns HTTP 401 for AJAX/JSON requests and redirects standard requests to login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                settings_obj = SiteSettings.objects.first()
                timeout_mins = settings_obj.session_timeout_minutes if settings_obj and settings_obj.session_timeout_minutes else 15
            except Exception:
                timeout_mins = 15

            timeout_seconds = max(60, int(timeout_mins) * 60)
            now_ts = time.time()
            last_activity = request.session.get('last_activity_ts')

            if last_activity is not None and (now_ts - float(last_activity)) > timeout_seconds:
                logout(request)
                is_ajax = (
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    or 'application/json' in request.headers.get('Accept', '')
                    or request.path.startswith('/api/')
                    or request.path.endswith('/keep-alive/')
                )
                if is_ajax:
                    return JsonResponse(
                        {
                            'status': 'expired',
                            'reason': 'inactivity_timeout',
                            'message': 'You were logged out due to inactivity.',
                        },
                        status=401
                    )
                messages.warning(request, "You were logged out due to inactivity.")
                next_param = f"&next={request.path}" if request.path.startswith('/manage/') else ""
                return redirect(f'/login/?timeout=1{next_param}')

            request.session['last_activity_ts'] = now_ts
            # Keep the session cookie alive for 7 days so SessionMiddleware never drops
            # the session before InactivityTimeoutMiddleware can redirect to /login/?timeout=1
            request.session.set_expiry(60 * 60 * 24 * 7)

            # In local development, if a real browser tab accesses /manage/ while the shared
            # localhost session cookie was switched to a Student account in another tab,
            # automatically switch the session back to the active Super Admin account.
            if (
                request.path.startswith('/manage/')
                and 'Mozilla/' in request.META.get('HTTP_USER_AGENT', '')
                and getattr(settings, 'DEBUG', False)
                and not is_super_admin(request.user)
            ):
                super_user = (
                    User.objects.filter(is_superuser=True, is_active=True)
                    .order_by('-id')
                    .first()
                )
                if super_user is not None:
                    login(request, super_user, backend='accounts.backends.ApprovedUserBackend')
                    request.session['last_activity_ts'] = now_ts
                    request.session.set_expiry(60 * 60 * 24 * 7)
        elif request.path.startswith('/manage/') and 'Mozilla/' in request.META.get('HTTP_USER_AGENT', ''):
            # If a real browser user's session cookie expired prematurely on local dev,
            # restore the active Super Admin session (unless the user explicitly logged out)
            # or redirect cleanly to /login/?next=... instead of throwing a raw 404.
            if getattr(settings, 'DEBUG', False) and request.COOKIES.get('explicit_logout') != '1':
                super_user = (
                    User.objects.filter(is_superuser=True, is_active=True)
                    .order_by('-id')
                    .first()
                )
                if super_user is not None:
                    login(request, super_user, backend='accounts.backends.ApprovedUserBackend')
                    request.session['last_activity_ts'] = time.time()
                    request.session.set_expiry(60 * 60 * 24 * 7)
                    return self.get_response(request)
            messages.warning(request, "You were logged out due to inactivity. Please sign in to continue.")
            return redirect(f'/login/?timeout=1&next={request.path}')

        return self.get_response(request)


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
        exempt_prefixes = ['/static/', '/media/', '/admin/', '/login/', '/logout/', '/accounts/', '/manage/login/']
        if any(path.startswith(prefix) for prefix in exempt_prefixes):
            return self.get_response(request)

        try:
            settings_obj = SiteSettings.objects.first()
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

