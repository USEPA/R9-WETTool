# Generated by Django 2.2.15 on 2021-01-11 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0037_auto_20201116_0933'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Categorie'},
        ),
        migrations.AddField(
            model_name='survey',
            name='assessment_layer',
            field=models.TextField(blank=True, null=True),
        ),
    ]
