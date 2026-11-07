"""
ASGI config for driving_school project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'driving_school.settings.dev')

application = get_asgi_application()
