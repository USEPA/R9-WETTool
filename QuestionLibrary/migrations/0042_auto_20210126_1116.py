# Generated by Django 2.2.15 on 2021-01-26 18:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0041_auto_20210125_1417'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='masterquestion',
            name='related_question',
        ),
        migrations.RemoveField(
            model_name='relatedquestion',
            name='answer',
        ),
        migrations.AddField(
            model_name='relatedquestionlist',
            name='relevant_field',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.Lookup'),
        ),
    ]