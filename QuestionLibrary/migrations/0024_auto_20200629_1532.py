# Generated by Django 3.0.7 on 2020-06-29 21:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0023_auto_20200629_0859'),
    ]

    operations = [
        migrations.RenameField(
            model_name='survey',
            old_name='map_service',
            new_name='base_map_service',
        ),
    ]
