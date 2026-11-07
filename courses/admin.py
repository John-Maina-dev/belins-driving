from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Course

@admin.register(Course)
class CourseAdmin(ImportExportModelAdmin):
    list_display = ('name', 'license_category', 'duration', 'fee', 'is_featured', 'is_active', 'order')
    list_filter = ('license_category', 'is_featured', 'is_active')
    search_fields = ('name', 'short_description', 'full_description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('fee', 'is_featured', 'is_active', 'order')
