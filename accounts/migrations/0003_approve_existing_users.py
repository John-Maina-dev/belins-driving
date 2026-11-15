from django.db import migrations

def approve_all_existing_users(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.all().update(approval_status='APPROVED')

def reverse_approve(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_userprofile_approval_status_userprofile_approved_at_and_more'),
    ]

    operations = [
        migrations.RunPython(approve_all_existing_users, reverse_approve),
    ]

