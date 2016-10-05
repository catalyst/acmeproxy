# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxy', '0004_auto_20161004_1514'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='authorisation',
            unique_together=set([('name', 'suffix_match')]),
        ),
    ]
