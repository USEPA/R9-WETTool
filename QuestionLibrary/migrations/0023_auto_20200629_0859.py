# Generated by Django 3.0.7 on 2020-06-29 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0022_auto_20200629_0854'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='masterquestion',
            name='sort_order',
        ),
        migrations.AddField(
            model_name='questionset',
            name='sort_order',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
