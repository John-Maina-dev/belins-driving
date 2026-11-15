from django.apps import AppConfig

class WebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website'
    verbose_name = 'Public Website & Content'

    def ready(self):
        from .signals import register_cleanup_signals
        register_cleanup_signals()
