# Generated by Django 2.2.15 on 2020-09-25 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0034_auto_20200925_1253'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='facilitytype',
            name='description',
        ),
        migrations.RemoveField(
            model_name='facilitytype',
            name='label',
        ),
        migrations.AddField(
            model_name='facilitytype',
            name='fac_code',
            field=models.CharField(blank=True, help_text='Facility Code', max_length=5, null=True, verbose_name='Fac Code'),
        ),
        migrations.AlterField(
            model_name='facilitytype',
            name='facility_type',
            field=models.CharField(blank=True, help_text='Facility Type', max_length=50, null=True),
        ),
    ]