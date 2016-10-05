# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxy', '0002_auto_20160930_1457'),
    ]

    operations = [
        migrations.RenameField(
            model_name='authorisation',
            old_name='prefix_match',
            new_name='suffix_match',
        ),
    ]
