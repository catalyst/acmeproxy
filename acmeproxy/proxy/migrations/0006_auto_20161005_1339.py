# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ("proxy", "0005_auto_20161005_1215"),
    ]

    operations = [
        migrations.AddField(
            model_name="authorisation",
            name="created_at",
            field=models.DateTimeField(
                default=datetime.datetime(2016, 10, 5, 0, 39, 2, 173677, tzinfo=utc),
                auto_now_add=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="authorisation",
            name="created_by_ip",
            field=models.GenericIPAddressField(
                default="192.0.2.1", verbose_name="Created by IP address"
            ),
            preserve_default=False,
        ),
    ]
