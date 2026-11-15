from django.db import migrations


def assign_existing_records_to_default_branch(apps, schema_editor):
    Branch = apps.get_model('courses', 'Branch')
    Course = apps.get_model('courses', 'Course')
    Instructor = apps.get_model('instructors', 'Instructor')
    Student = apps.get_model('students', 'Student')

    has_records = (
        Course.objects.exists()
        or Instructor.objects.exists()
        or Student.objects.exists()
    )
    if not has_records:
        return

    default_branch, _ = Branch.objects.get_or_create(
        code='MAIN-NRB',
        defaults={
            'name': 'Main Campus - Nairobi',
            'address': 'Moi Avenue, Nairobi',
            'town': 'Nairobi',
            'phone': '+254 700 123 456',
            'email': 'info@belingsdriving.co.ke',
            'opening_hours': 'Mon - Fri: 7:00 AM - 6:30 PM | Sat: 8:00 AM - 4:00 PM',
            'is_active': True,
            'order': 1,
        }
    )

    for course in Course.objects.all():
        if not course.branches.exists():
            course.branches.add(default_branch)

    Instructor.objects.filter(branch__isnull=True).update(branch=default_branch)
    Student.objects.filter(branch__isnull=True).update(branch=default_branch)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_branch_course_branches_vehicle'),
        ('instructors', '0003_instructor_branch'),
        ('students', '0003_student_branch_alter_student_date_of_birth_and_more'),
    ]

    operations = [
        migrations.RunPython(assign_existing_records_to_default_branch, reverse_noop),
    ]

