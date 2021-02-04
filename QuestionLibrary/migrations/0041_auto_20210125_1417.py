# Generated by Django 2.2.15 on 2021-01-25 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0040_auto_20210125_1408'),
    ]

    operations = [
        migrations.AddField(
            model_name='masterquestion',
            name='related_question',
            field=models.ManyToManyField(blank=True, related_name='_masterquestion_related_question_+', to='QuestionLibrary.MasterQuestion'),
        ),
        migrations.AlterField(
            model_name='relatedquestion',
            name='questions',
            field=models.ManyToManyField(related_name='related_questions', through='QuestionLibrary.RelatedQuestionList', to='QuestionLibrary.MasterQuestion'),
        ),
    ]
