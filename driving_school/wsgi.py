"""
WSGI config for driving_school project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'driving_school.settings.dev')

application = get_wsgi_application()
