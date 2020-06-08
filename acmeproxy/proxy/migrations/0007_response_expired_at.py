# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proxy", "0006_auto_20161005_1339"),
    ]

    operations = [
        migrations.AddField(
            model_name="response",
            name="expired_at",
            field=models.DateTimeField(null=True),
        ),
    ]
