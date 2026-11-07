from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Instructor

@admin.register(Instructor)
class InstructorAdmin(ImportExportModelAdmin):
    list_display = ('full_name', 'title', 'license_categories', 'experience_years', 'is_featured', 'is_active', 'order')
    list_filter = ('is_featured', 'is_active')
    search_fields = ('full_name', 'title', 'license_categories', 'bio')
    list_editable = ('is_featured', 'is_active', 'order')

