from django.db import models
from django.conf import settings
from django.db.models import F
import shutil
import pandas as pd
import os
import re
from social_django.utils import load_strategy
from django.contrib.auth.models import User
import requests, json
from django.core.exceptions import ValidationError


class LookupAbstract(models.Model):
    label = models.CharField(max_length=50, help_text='This is a test')
    description = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        description = f" ({self.description})" if self.description is not None else ''
        return f"{self.label}{description}"

    @property
    def formatted_survey_name(self):
        return re.sub(r'[^a-zA-Z\d\s:]', '', self.label.lower()).replace(" ", "_")

    class Meta:
        abstract = True


class LookupGroup(LookupAbstract):
    pass


class Lookup(LookupAbstract):
    group = models.ForeignKey('LookupGroup', on_delete=models.CASCADE, related_name='lookups')


class Media(LookupAbstract):
    pass


# todo: if this is to be more generic then Water should not be used here... SubType perhaps is better?
class FacilitySubType(LookupAbstract):
    pass


class FacilityType(LookupAbstract):
    pass


# todo: more like default config of logic.. rename?
# todo: allow matching of these to fields in the actual data set
class Category(LookupAbstract):
    media = models.ForeignKey('Media', on_delete=models.PROTECT)
    facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT)
    sub_facility_type = models.ForeignKey('FacilitySubType', on_delete=models.PROTECT)


# todo: more closely link this with survey123.  Maybe allow input of the cross walk so its configurable and dynamic

class ResponseType(LookupAbstract):
    pass

    survey123_field_type = models.CharField(max_length=50)


class Unit(LookupAbstract):
    pass


class FeatureServiceResponse(models.Model):
    fs_response_type = models.CharField(max_length=250)
    esri_field_type = models.CharField(max_length=250)

    def __str__(self):
        return self.fs_response_type


class MasterQuestion(models.Model):
    question = models.TextField(max_length=1000)

    # todo: why is media here and in category
    media = models.ForeignKey('Media', on_delete=models.PROTECT)
    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    response_type = models.ForeignKey('ResponseType', on_delete=models.PROTECT)
    lookup = models.ForeignKey('LookupGroup', on_delete=models.PROTECT, null=True, blank=True)
    # todo: triggers creation of second field for survey generation if not none
    default_unit = models.ForeignKey('Lookup', on_delete=models.PROTECT, null=True, blank=True,
                                     help_text='To set a default vales ..... etc')

    # todo: does question active make sense in here or just in the survey itself?
    # question_active = models.BooleanField(default=True)

    # sort_order = models.IntegerField(null=True, blank=True)

    # todo: add question hint
    # todo: is anything or everything required

    def __str__(self):
        return self.question

    @property
    def formatted_survey_field_type(self):
        if self.response_type.survey123_field_type == 'select_one':
            return f"{self.response_type.survey123_field_type} {self.lookup.formatted_survey_name}"
        # could add more here but nothing useful I can see right now
        # values = {'list_name': self.lookup.formatted_survey_name}
        # return self.response_type.survey123_field_type.format(**values)
        return self.response_type.survey123_field_type

    @property
    def formatted_survey_field_name(self):
        return re.sub(r'[^a-zA-Z\d\s:]', '', self.question.lower()).replace(" ", "_")

    @property
    def formatted_survey_field_relevant(self):
        if self.question == "Media":
            return
        return f"${{media}}='{self.media.label}'"

    def get_formatted_question(self):
        # must always return a list
        if self.lookup is not None and self.response_type.survey123_field_type != 'select_one':
            return [{
                'type': 'begin_group',
                'name': self.formatted_survey_field_name,
                'label': self.question,
                'relevant': self.formatted_survey_field_relevant,
            },
                {
                    'type': self.formatted_survey_field_type,
                    'name': f'{self.formatted_survey_field_name}_measure',
                    'label': 'Measure'
                },
                {
                    'type': f'select_one {self.lookup}',
                    'name': f'{self.formatted_survey_field_name}_choices',
                    'label': self.lookup.description,
                    'default': getattr(self.default_unit, 'label', None)
                },
                {
                    'type': 'end group'
                }

            ]

        return [{
            'type': self.formatted_survey_field_type,
            'name': self.formatted_survey_field_name,
            'label': self.question,
            'relevant': self.formatted_survey_field_relevant,
        }]


class Survey(models.Model):
    name = models.CharField(max_length=250)
    # todo: determine how to select this and then make fields available for matching to category values
    # perhaps this is a url to a published service?
    # this way the data doesn't even need to be on same machine or network. could even be in agol
    base_map_service = models.URLField()
    survey123_service = models.URLField(null=True)

    # the querying the service based on extent or values would be much more straight forward
    # todo: limit the results of the data source to only select a subset.  This is for creating preload survey

    # store the fields from the service locally for reference in forms?
    service_config = models.TextField(null=True, blank=True)

    # media = models.ForeignKey('Media', on_delete=models.PROTECT)
    # facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT)
    # sub_facility_type = models.ForeignKey('FacilitySubType', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    survey123_translation = {

        'name': 'formatted_survey_field_name',
        'label': 'question',

    }

    def generate_xlsform(self):
        template = os.path.join(settings.BASE_DIR, settings.XLS_FORM_TEMPLATE)
        output_survey = os.path.join(settings.BASE_DIR, f'QuestionLibrary\\generated_forms\\{self.id}.xlsx')
        shutil.copy(template, output_survey)
        orig_survey_df = pd.read_excel(output_survey, sheet_name='survey')
        orig_choices_df = pd.read_excel(output_survey, sheet_name='choices')
        assigned_questions = MasterQuestion.objects.filter(question_set__surveys=self)
        feat_service = json.loads(self.service_config)

        fields = [
            {
                'type': FeatureServiceResponse.objects.get(fs_response_type=y['type']).esri_field_type,
                'name': y['name'],
                'label': y['alias']
            } for x in feat_service for y in x['fields']
        ]

        field_df = pd.DataFrame(fields)
        field_df_drop_dups = field_df.drop_duplicates()

        group_header = [
            {
                'type': 'begin_group',
                'name': 'begin_group',
                'label': x.question
            } for x in assigned_questions if LookupGroup.objects.filter(label=x.lookup)
        ]
        group_df = pd.DataFrame(group_header)
        end_group = {'type': 'end group'}
        for row in group_df['type']:
            if row == 'begin_group':
                group_df.append(end_group, ignore_index=True)

        questions = []
        for x in assigned_questions:
            questions.extend(x.get_formatted_question())

        # if questions has units
        # label = x.question
        # type = begin_group
        # name = begin_group
        # add 2 new fields:
        # label = Value
        # type = integer
        # name = value
        # label = Units
        # type = select_one (lookup)
        # name = units

        questions_df = pd.DataFrame(questions)
        survey_df_all = [questions_df, group_df, field_df_drop_dups]
        survey_df = orig_survey_df.append(survey_df_all)

        assigned_lookups = Lookup.objects.filter(group__masterquestion__question_set__surveys=self).distinct()
        choices = [
            {
                'list_name': x.group.formatted_survey_name,
                'name': x.formatted_survey_name,
                'label': x.description,
            } for x in assigned_lookups
        ]
        fs_lookup = FeatureServiceResponse.objects.all().distinct()
        fs_choices = [
            {
                'list_name': x.esri_field_type,
                'name': x.esri_field_type,
                'label': x.fs_response_type

            } for x in fs_lookup
        ]
        lookups_df = pd.DataFrame(choices)
        fs_lookups_df = pd.DataFrame(fs_choices)
        lookups_all = [lookups_df, fs_lookups_df]
        choices_df = orig_choices_df.append(lookups_all)

        with pd.ExcelWriter(output_survey, mode='w') as writer:
            survey_df.to_excel(writer, sheet_name='survey', index=False)
            choices_df.to_excel(writer, sheet_name='choices', index=False)
        # return questions_df, choices_df

    def getMapService(self, user):
        if not self.service_config:
            layers = []
            social = user.social_auth.get(provider='agol')
            token = social.get_access_token(load_strategy())
            r = requests.get(url=self.base_map_service, params={'token': token, 'f': 'json'})
            for x in r.json()['layers']:
                q = requests.get(url=self.base_map_service + '/' + str(x['id']), params={'token': token, 'f': 'json'})
                layers.append(q.json())
            for f in r.json()['tables']:
                q = requests.get(url=self.base_map_service + '/' + str(f['id']), params={'token': token, 'f': 'json'})
                layers.append(q.json())

            self.service_config = json.dumps(layers)

    class Meta:
        verbose_name = "Assessment"


# todo: figure out how to publish survey123. it might have to be manual


class QuestionSet(models.Model):
    name = models.CharField(max_length=250)
    owner = models.CharField(max_length=250)
    surveys = models.ManyToManyField('Survey', related_name='question_set')
    questions = models.ManyToManyField('MasterQuestion', related_name='question_set', through='QuestionList')
    sort_order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    # todo: change the surveys many to many field back to a relationship table


class QuestionList(models.Model):
    set = models.ForeignKey('QuestionSet', on_delete=models.PROTECT)
    question = models.ForeignKey('MasterQuestion', on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(null=True, blank=True)

# class Job(models.Model):
#     name = models.CharField(max_length=250)
#     job_date = models.DateTimeField()
#     job_due_date = models.DateTimeField()
#     assessment = models.ManyToManyField('Survey')
