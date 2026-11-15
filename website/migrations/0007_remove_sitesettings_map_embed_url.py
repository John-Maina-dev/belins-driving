from django.db import migrations

DEFAULT_ADDRESS = "Ouru Power building, Kisii Town, Kisii County"


def fix_demo_address(apps, schema_editor):
    """Replace only the seeded Nairobi demo address; never touch an address staff typed."""
    SiteSettings = apps.get_model('website', 'SiteSettings')
    for s in SiteSettings.objects.all():
        address = (s.address or '')
        if 'belings towers' in address.lower() and 'nairobi' in address.lower():
            s.address = DEFAULT_ADDRESS
            s.save(update_fields=['address'])


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0006_galleryimage_image_grid_galleryimage_image_large_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_demo_address, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='sitesettings',
            name='map_embed_url',
        ),
    ]

