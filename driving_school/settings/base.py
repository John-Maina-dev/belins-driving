"""
Base settings for driving_school project.
Shared across development and production environments.
"""
from pathlib import Path
from decouple import config, Csv
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

SECRET_KEY = config('SECRET_KEY', default='django-insecure-default-change-me')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'import_export',
    'django_filters',
    'simple_history',
]

LOCAL_APPS = [
    'accounts.apps.AccountsConfig',
    'manage_panel.apps.ManagePanelConfig',
    'website.apps.WebsiteConfig',
    'courses.apps.CoursesConfig',
    'instructors.apps.InstructorsConfig',
    'students.apps.StudentsConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'driving_school.middleware.InactivityTimeoutMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'driving_school.middleware.MaintenanceModeMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

ROOT_URLCONF = 'driving_school.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'website.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'driving_school.wsgi.application'
ASGI_APPLICATION = 'driving_school.asgi.application'

# Database configuration
# Defaults to SQLite in development, uses DATABASE_URL if provided
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
if dj_database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL', default=DEFAULT_DATABASE_URL),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
if DATABASES['default'].get('ENGINE') == 'django.db.backends.sqlite3':
    DATABASES['default'].setdefault('OPTIONS', {})['timeout'] = 30

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.ApprovedUserBackend',
]

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True

# Currency
CURRENCY_CODE = 'KES'
CURRENCY_SYMBOL = 'KES '

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (user uploads) - configurable via MEDIA_ROOT in .env (e.g. outside OneDrive)
MEDIA_URL = '/media/'
_custom_media_root = config('MEDIA_ROOT', default='').strip()
MEDIA_ROOT = Path(_custom_media_root) if _custom_media_root else (BASE_DIR / 'media')

# File upload size and count limits
DATA_UPLOAD_MAX_MEMORY_SIZE = 150 * 1024 * 1024   # 150 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024    # 50 MB in memory buffer
DATA_UPLOAD_MAX_NUMBER_FILES = 200                # Allow batch upload of up to 200 files at once

# WhiteNoise storage configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# M-Pesa Daraja Settings
MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='')
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')
MPESA_PASSKEY = config('MPESA_PASSKEY', default='')
MPESA_INITIATOR_NAME = config('MPESA_INITIATOR_NAME', default='')
MPESA_INITIATOR_PASSWORD = config('MPESA_INITIATOR_PASSWORD', default='')
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='')

# SMS Gateway Settings
SMS_PROVIDER = config('SMS_PROVIDER', default='africastalking')
SMS_USERNAME = config('SMS_USERNAME', default='sandbox')
SMS_API_KEY = config('SMS_API_KEY', default='')
SMS_SENDER_ID = config('SMS_SENDER_ID', default='')

# Session Configuration (Auto logout after 15 minutes of inactivity)
SESSION_COOKIE_AGE = 900  # 15 minutes in seconds
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Email notification configuration (Dynamic database SMTP with console fallback)
EMAIL_BACKEND = 'driving_school.email_backend.DatabaseEmailBackend'
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='info@belingsdriving.co.ke')
CONTACT_NOTIFICATION_EMAIL = config('CONTACT_NOTIFICATION_EMAIL', default='admin@belingsdriving.co.ke')
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default='')
