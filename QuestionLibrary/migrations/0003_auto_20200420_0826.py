# Generated by Django 3.0.5 on 2020-04-20 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0002_auto_20200420_0820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lookup',
            name='description',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
