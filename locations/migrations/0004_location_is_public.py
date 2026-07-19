# Adds Ownable.is_public (lets an owner make a detail page viewable by
# anonymous/logged-out visitors; default False keeps current behavior).
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0003_alter_location_uuid_alter_locationtrack_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='is_public',
            field=models.BooleanField(default=False, help_text='Anyone can view this page without logging in.', verbose_name='Publicly viewable'),
        ),
    ]
