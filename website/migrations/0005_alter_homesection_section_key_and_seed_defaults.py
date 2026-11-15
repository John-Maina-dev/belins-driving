from django.db import migrations, models


DEFAULT_SECTIONS = [
    ('hero', 'Hero Slider / Banner', 1),
    ('stats', 'Statistics Counters', 2),
    ('about', 'About Us & Mission', 3),
    ('courses', 'Featured Courses', 4),
    ('branches', 'Campus Branches & Locations', 5),
    ('gallery', 'Photo Gallery Showcase', 6),
    ('why_choose_us', 'Why Choose Belings', 7),
    ('testimonials', 'Student Testimonials', 8),
    ('instructors', 'Instructors Preview', 9),
    ('faqs', 'Frequently Asked Questions', 10),
    ('cta', 'Enrollment Call to Action', 11),
    ('contact', 'Contact & Location Summary', 12),
]


def seed_home_sections(apps, schema_editor):
    HomeSection = apps.get_model('website', 'HomeSection')
    if HomeSection.objects.filter(section_key='why_us').exists() and not HomeSection.objects.filter(section_key='why_choose_us').exists():
        HomeSection.objects.filter(section_key='why_us').update(section_key='why_choose_us')

    for key, title, default_order in DEFAULT_SECTIONS:
        HomeSection.objects.get_or_create(
            section_key=key,
            defaults={
                'title': title,
                'order': default_order,
                'is_enabled': True,
            },
        )


def reverse_seed_home_sections(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_rename_reply_to_emailsettings_reply_to_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homesection',
            name='section_key',
            field=models.CharField(
                choices=[
                    ('hero', 'Hero Slider / Banner'),
                    ('stats', 'Statistics Counters'),
                    ('about', 'About Us & Mission'),
                    ('courses', 'Featured Courses'),
                    ('branches', 'Campus Branches & Locations'),
                    ('gallery', 'Photo Gallery Showcase'),
                    ('why_choose_us', 'Why Choose Belings'),
                    ('why_us', 'Why Choose Belings'),
                    ('testimonials', 'Student Testimonials'),
                    ('instructors', 'Instructors Preview'),
                    ('faqs', 'Frequently Asked Questions'),
                    ('cta', 'Enrollment Call to Action'),
                    ('contact', 'Contact & Location Summary'),
                ],
                max_length=50,
                unique=True,
            ),
        ),
        migrations.RunPython(seed_home_sections, reverse_seed_home_sections),
    ]

