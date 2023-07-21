from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.db.models import F


def copy_field_types(apps, schema):
    ResponseTypeModel = apps.get_model('QuestionLibrary', 'ResponseType')
    Survery123FieldTypeModel = apps.get_model('QuestionLibrary', 'Survey123FieldType')
    for i in ResponseTypeModel.objects.all():
        Survery123FieldTypeModel.objects.create(
            pk=i.pk,
            label=i.label,
            description=i.description,
            field_type=i.survey123_field_type,
        )


def copy_relationships(apps, schema):
    MasterQuestionModel = apps.get_model('QuestionLibrary', 'MasterQuestion')
    MasterQuestionModel.objects.all().update(survey123_field_type=F('response_type'))


class Migration(migrations.Migration):
    dependencies = [
        ('QuestionLibrary', '0046_auto_20230608_1122'),
    ]

    operations = [
        migrations.CreateModel(
            name='EPAResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='EPA Response Name', max_length=150, null=True)),
                ('map_service_url', models.URLField(help_text='Enter a valid service URL, then click "save and continue editing" to get the service config.', null=True, verbose_name='Base Map Service')),
                ('map_service_config', models.TextField(null=True, blank=True)),
                ('system_layer_id', models.IntegerField(default=0, null=True, verbose_name='System Layer')),
                ('facility_layer_id', models.IntegerField(default=1, null=True, verbose_name='Facility Layer')),
                ('assessment_table_id', models.IntegerField(default=2, null=True, verbose_name='Responses Table')),
                ('disabled_date', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'verbose_name': 'EPA Response',
            },
        ),
        migrations.CreateModel(
            name='Survey123FieldType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='like this', max_length=50)),
                ('description', models.CharField(blank=True, max_length=500, null=True)),
                ('field_type', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Survey123 Field Type',
            },
        ),
        migrations.RunPython(
            code=copy_field_types
        ),
        migrations.RenameModel(
            old_name='FeatureServiceResponse',
            new_name='ESRIFieldTypes',
        ),
        migrations.AddField(
            model_name='masterquestion',
            name='survey123_field_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.survey123fieldtype',
                                    verbose_name='Survey123 Field Type'),
        ),
        migrations.RunPython(
            code=copy_relationships
        ),
        migrations.AlterModelOptions(
            name='lookupgroup',
            options={'verbose_name': 'Answer Choices'},
        ),
        migrations.RenameField(
            model_name='esrifieldtypes',
            old_name='esri_field_type',
            new_name='data_type',
        ),
        migrations.RenameField(
            model_name='esrifieldtypes',
            old_name='fs_response_type',
            new_name='field_type',
        ),
        migrations.RemoveField(
            model_name='masterquestion',
            name='response_type',
        ),
        # migrations.RemoveField(
        #     model_name='questionset',
        #     name='category',
        # ),
        # migrations.RemoveField(
        #     model_name='questionset',
        #     name='facility_type',
        # ),
        # migrations.RemoveField(
        #     model_name='questionset',
        #     name='media',
        # ),
        migrations.AlterField(
            model_name='masterquestion',
            name='default_unit',
            field=models.ForeignKey(blank=True,
                                    help_text='To generate a list of default values, select desired question type and click "Save and Continue Editing"',
                                    null=True, on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.lookup'),
        ),
        migrations.AlterField(
            model_name='masterquestion',
            name='lookup',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.lookupgroup',
                                    verbose_name='Answer Type'),
        ),
        migrations.AlterField(
            model_name='masterquestion',
            name='category',
            field=models.ForeignKey(blank=True, help_text='Leaving category type empty will apply the question to ALL category types.', null=True,
                                    on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.category'),
        ),
        migrations.AlterField(
            model_name='masterquestion',
            name='facility_type',
            field=models.ForeignKey(blank=True, help_text='Leaving facility type empty will apply the question to ALL facility types.', null=True,
                                    on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.facilitytype'),
        ),
        migrations.AlterField(
            model_name='relatedquestionlist',
            name='relevant_field',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='QuestionLibrary.lookup'),
        ),
        migrations.DeleteModel(
            name='ResponseType',
        ),
        migrations.AddField(
            model_name='survey',
            name='epa_response',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='QuestionLibrary.eparesponse',
                                    help_text='Select an EPA response and click "Save and Continue Editing" before proceeding.'),
        ),
        migrations.AlterField(
            model_name='survey',
            name='layer',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='survey',
            name='assessment_layer',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
