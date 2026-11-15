from django.db import migrations, models
import django.core.validators
from decimal import Decimal

DEFAULT_ADDRESS = "Ouru Power building, Kisii Town, Kisii County"
DEFAULT_TOWN = "Kisii"
# UNVERIFIED default: staff must confirm the pin is on the right building.
DEFAULT_EMBED = "https://www.google.com/maps?q=Ouru+Power+Kisii&output=embed"


def migrate_map_data(apps, schema_editor):
    from courses.map_utils import normalize_map_embed_url
    from django.core.exceptions import ValidationError

    Branch = apps.get_model('courses', 'Branch')

    # 1. Carry over any old map_link value that is a valid Google Maps link; drop everything else.
    for branch in Branch.objects.all():
        try:
            cleaned = normalize_map_embed_url(branch.map_link)
        except ValidationError:
            cleaned = ''
        if cleaned != (branch.map_embed_url or ''):
            branch.map_embed_url = cleaned
            branch.save(update_fields=['map_embed_url'])

    # 2. Main branch defaults (only when it has no map yet and still carries the Nairobi demo data).
    main = Branch.objects.order_by('order', 'pk').first()
    if main and not main.map_embed_url and main.latitude is None and main.longitude is None:
        text = f"{main.name} {main.address} {main.town}".lower()
        if not (main.address or '').strip() or 'nairobi' in text:
            main.address = DEFAULT_ADDRESS
            main.town = DEFAULT_TOWN
            main.map_embed_url = DEFAULT_EMBED
            if 'nairobi' in main.name.lower():
                main.name = main.name.replace('Nairobi', DEFAULT_TOWN).replace('nairobi', DEFAULT_TOWN)
            new_code = main.code.upper().replace('NRB', 'KSI')
            if new_code != main.code.upper() and not Branch.objects.filter(code=new_code).exists():
                main.code = new_code
            main.save()


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_branch_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='map_embed_url',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='branch',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True,
                                      validators=[django.core.validators.MinValueValidator(Decimal('-90')), django.core.validators.MaxValueValidator(Decimal('90'))]),
        ),
        migrations.AddField(
            model_name='branch',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True,
                                      validators=[django.core.validators.MinValueValidator(Decimal('-180')), django.core.validators.MaxValueValidator(Decimal('180'))]),
        ),
        migrations.AddField(
            model_name='branch',
            name='map_zoom',
            field=models.PositiveSmallIntegerField(default=16, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(21)]),
        ),
        migrations.RunPython(migrate_map_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='branch',
            name='map_link',
        ),
        migrations.AlterField(
            model_name='branch',
            name='town',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
