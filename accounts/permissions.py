from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
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
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/admin/login/?next={request.path}")
        if not is_super_admin(request.user):
            raise PermissionDenied("Access denied. This action requires Super Administrator privileges.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def management_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/admin/login/?next={request.path}")
        if not is_management_authorized(request.user):
            raise PermissionDenied("Access denied. Only School Administrators and Super Administrators can access the management panel.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class ManagementRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is an Admin or Super Admin."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_management_authorized(request.user):
            raise PermissionDenied("Access denied. Management authorization required.")
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(AccessMixin):
    """Verify that the current user is a Super Admin."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_super_admin(request.user):
            raise PermissionDenied("Access denied. Super Administrator authorization required.")
        return super().dispatch(request, *args, **kwargs)

