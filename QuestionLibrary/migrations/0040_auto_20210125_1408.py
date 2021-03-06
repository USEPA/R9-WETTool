# Generated by Django 2.2.15 on 2021-01-25 21:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('QuestionLibrary', '0039_auto_20210113_1249'),
    ]

    operations = [
        migrations.CreateModel(
            name='RelatedQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='masterquestion',
            options={'verbose_name': 'Master Question'},
        ),
        migrations.CreateModel(
            name='RelatedQuestionList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.MasterQuestion')),
                ('related', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.RelatedQuestion')),
            ],
        ),
        migrations.AddField(
            model_name='relatedquestion',
            name='questions',
            field=models.ManyToManyField(related_name='related_question', through='QuestionLibrary.RelatedQuestionList', to='QuestionLibrary.MasterQuestion'),
        ),
    ]
