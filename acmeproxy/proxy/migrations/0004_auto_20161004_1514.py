# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proxy", "0003_auto_20161004_1402"),
    ]

    operations = [
        migrations.RenameField(
            model_name="response", old_name="created", new_name="created_at",
        ),
        migrations.AlterField(
            model_name="response",
            name="created_by_ip",
            field=models.GenericIPAddressField(verbose_name="Created by IP address"),
        ),
    ]
