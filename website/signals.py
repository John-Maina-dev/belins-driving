import os
from django.db.models.signals import pre_save, post_delete, post_migrate
from django.dispatch import receiver
from django.db import models

def _delete_file(file_obj):
    if file_obj and hasattr(file_obj, 'path'):
        try:
            if os.path.isfile(file_obj.path):
                os.remove(file_obj.path)
        except (OSError, IOError):
            pass

def cleanup_pre_save(sender, instance, **kwargs):
    """When a model is updated, delete the old file if it has changed or been removed."""
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    for field in instance._meta.fields:
        if isinstance(field, (models.FileField, models.ImageField)):
            old_file = getattr(old_instance, field.name)
            new_file = getattr(instance, field.name)
            if old_file and old_file != new_file:
                _delete_file(old_file)

def cleanup_post_delete(sender, instance, **kwargs):
    """When a model is deleted, delete its associated files on disk."""
    for field in instance._meta.fields:
        if isinstance(field, (models.FileField, models.ImageField)):
            file_obj = getattr(instance, field.name)
            _delete_file(file_obj)

def ensure_defaults_post_migrate(sender, **kwargs):
    """Ensure standard HomeSection rows exist after migrations without overwriting admin settings."""
    try:
        from website.models import HomeSection
        HomeSection.ensure_defaults()
    except Exception:
        pass

def register_cleanup_signals():
    """Register cleanup handlers on all models that contain file/image fields, plus post_migrate defaults."""
    from django.apps import apps
    target_models = [
        'website.SiteSettings',
        'website.HeroSlide',
        'website.GalleryImage',
        'website.Testimonial',
        'courses.Course',
        'courses.Branch',
        'instructors.Instructor',
        'accounts.UserProfile',
    ]
    for model_name in target_models:
        try:
            model = apps.get_model(model_name)
            pre_save.connect(cleanup_pre_save, sender=model, weak=False)
            post_delete.connect(cleanup_post_delete, sender=model, weak=False)
        except (LookupError, ValueError):
            pass

    try:
        website_app = apps.get_app_config('website')
        post_migrate.connect(ensure_defaults_post_migrate, sender=website_app, weak=False)
    except LookupError:
        pass


