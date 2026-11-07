from django.contrib import admin, messages
from import_export.admin import ImportExportModelAdmin
from .models import Student

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    list_display = (
        'full_name', 'phone', 'email', 'course', 'preferred_schedule',
        'preferred_branch', 'status', 'created_at'
    )
    list_filter = ('status', 'course', 'preferred_schedule', 'preferred_branch', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'id_number')
    list_editable = ('status',)
    actions = ['approve_enrollment', 'mark_enrolled', 'mark_completed']

    @admin.action(description="Approve selected student enrollments")
    def approve_enrollment(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} student application(s) marked as Approved.", messages.SUCCESS)

    @admin.action(description="Mark selected students as Enrolled & Active")
    def mark_enrolled(self, request, queryset):
        updated = queryset.update(status='enrolled')
        self.message_user(request, f"{updated} student(s) marked as Enrolled.", messages.SUCCESS)

    @admin.action(description="Mark selected students as Completed / Graduated")
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} student(s) marked as Completed.", messages.SUCCESS)
