from functools import wraps
from django.http import Http404
from django.contrib.auth.mixins import AccessMixin

def get_user_role(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'SUPER_ADMIN'
    profile = getattr(user, 'profile', None)
    return profile.role if profile else None

def is_super_admin(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or get_user_role(user) == 'SUPER_ADMIN'

def is_management_authorized(user):
    """Super Admin and Admin have access to the management panel."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or get_user_role(user) in ['SUPER_ADMIN', 'ADMIN']


def super_admin_required(view_func):
    """Raise 404 for any user who is not a Super Admin so management routes are undiscoverable."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_super_admin(request.user):
            raise Http404("Page not found")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def management_required(view_func):
    """Raise 404 for anonymous users and non-management roles (student, instructor, receptionist)."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_management_authorized(request.user):
            raise Http404("Page not found")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class ManagementRequiredMixin(AccessMixin):
    """Verify that the current user is an Admin or Super Admin; otherwise raise 404."""
    def dispatch(self, request, *args, **kwargs):
        if not is_management_authorized(request.user):
            raise Http404("Page not found")
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(AccessMixin):
    """Verify that the current user is a Super Admin; otherwise raise 404."""
    def dispatch(self, request, *args, **kwargs):
        if not is_super_admin(request.user):
            raise Http404("Page not found")
        return super().dispatch(request, *args, **kwargs)


