# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxy', '0007_response_expired_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='authorisation',
            name='account',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='response',
            name='expired_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
