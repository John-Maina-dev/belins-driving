"""
driving_school URL Configuration
"""
from functools import wraps
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from decouple import config
from accounts import views as accounts_views
from students import views as students_views

# Custom Admin Site Branding
admin.site.site_header = "Belings Driving School Administration"
admin.site.site_title = "Belings Driving School Admin Portal"
admin.site.index_title = "School Management & Administration"

# Protect Django admin so unauthorized/anonymous users receive 404 (undiscoverable)
_orig_admin_view = admin.site.admin_view

def _protected_admin_view(view, cacheable=False):
    inner = _orig_admin_view(view, cacheable)
    @wraps(inner)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_active and request.user.is_staff):
            raise Http404("Page not found")
        return inner(request, *args, **kwargs)
    return wrapper

admin.site.admin_view = _protected_admin_view

admin_prefix = config('ADMIN_URL', default='admin/').strip('/') + '/'

urlpatterns = [
    path(admin_prefix, admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('login/', accounts_views.login_view, name='login'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('register/', accounts_views.register_view, name='register'),
    path('students/', include('students.urls', namespace='students')),
    path('dashboard/', students_views.dashboard_view, name='student_dashboard'),
    path('manage/', include('manage_panel.urls', namespace='manage')),
    path('courses/', include('courses.urls', namespace='courses')),
    path('', include('website.urls', namespace='website')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])


