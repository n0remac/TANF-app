import django.db.models.deletion
from django.db import migrations, models

import logging
logger = logging.getLogger(__name__)

def remove_federal_stt(apps, schema_editor):
    STT=apps.get_model('stts','STT')
    # We're getting rid of the explicit Federal government stt/location
    # From now on, users with no location are implicitly assumed to be
    # from the federal government.

    try:

        # With no explicitly federal users, we expect this line to fail.
        # This would always be the case in the test enviornment,
        # As the populate_stts command is run after migrations,
        # and the test environment would not be previously populated.
        federal_stt=STT.objects.get(name='Federal Government')

        User=apps.get_model('users','User')
        federal_stt_users=User.objects.filter(stt=federal_stt.id)

        for user in federal_stt_users:
            user.location_type = None
            user.location_id = None
    except STT.DoesNotExist:
        logger.info("No Federal Government STT users to migrate.")


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0029_use_location'),
        ('users', '0030_remove_add_user_permission_admin'),
        ('stts', '0002_auto_20200923_1809'),
    ]
    operations = [
        migrations.RunPython(remove_federal_stt)
    ]
