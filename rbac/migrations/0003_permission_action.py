# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2020-05-10 15:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0002_auto_20200510_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='action',
            field=models.CharField(default='', max_length=32),
        ),
    ]
