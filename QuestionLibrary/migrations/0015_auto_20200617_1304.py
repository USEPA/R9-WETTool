# Generated by Django 3.0.7 on 2020-06-17 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0013_auto_20200616_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionlist',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
