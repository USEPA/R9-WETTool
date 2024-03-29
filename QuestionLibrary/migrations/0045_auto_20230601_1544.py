# Generated by Django 3.2.19 on 2023-06-01 22:44

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0044_auto_20230523_1151'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('draft_id', models.UUIDField()),
                ('production_id', models.UUIDField()),
                ('base_feature_service', models.URLField()),
                ('draft_service_view', models.URLField()),
                ('production_service_view', models.URLField()),
            ],
        ),
    ]
