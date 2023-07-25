from django.db import models
from django.conf import settings
from django.db.models import F
import shutil
import pandas as pd
import os
import re

from django.utils.safestring import mark_safe
from social_django.utils import load_strategy
from django.contrib.auth.models import User
import requests
import json
from urllib.parse import urlencode
from itertools import islice
from django.core.exceptions import ValidationError
import csv
from django.utils.html import format_html
import uuid

from QuestionLibrary.func import formattedFieldName, get_service_config


class LookupAbstract(models.Model):
    label = models.CharField(max_length=50, help_text='like this')
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
    # group of answer choices (Answer Type) for a survey question
    pass

    class Meta:
        verbose_name = "Answer Choices"


class Lookup(LookupAbstract):
    # individual answer choice (question response)
    group = models.ForeignKey('LookupGroup', on_delete=models.CASCADE, related_name='lookups')


class Media(LookupAbstract):
    pass
    # class Meta:
    #     verbose_name = '1. Media'


# # todo: if this is to be more generic then Water should not be used here... SubType perhaps is better?
# class FacilitySubType(LookupAbstract):
#     pass


class EPAResponse(models.Model):
    name = models.CharField(max_length=150, help_text='EPA Response Name', null=True)
    map_service_url = models.URLField(verbose_name='Base Map Service', null=True,
                                      help_text='Enter a valid service URL, then click "save and continue editing" to get the service config.')
    # store the JSON service config from the service locally for reference in forms
    map_service_config = models.TextField(null=True, blank=True)
    system_layer_id = models.IntegerField(verbose_name='System Layer', null=True, default=0)
    facility_layer_id = models.IntegerField(verbose_name='Facility Layer', null=True, default=1)
    assessment_table_id = models.IntegerField(verbose_name='Responses Table', null=True, default=2)
    disabled_date = models.DateTimeField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_map_service(self, user):
        if self.map_service_url is not None:
            self.map_service_config = get_service_config(user=user, service=self.map_service_url)

    def get_layers_as_choices(self):
        config = json.loads(self.map_service_config)
        return [(layer['id'], layer['name']) for layer in config['layers']]

    def get_tables_as_choices(self):
        config = json.loads(self.map_service_config)
        return [(table['id'], table['name']) for table in config['tables']]

    def _map_service_config(self):
        if self.map_service_config is None:
            return '-'
        else:
            config = json.loads(self.map_service_config)
            if 'error' in config:
                return 'Error getting configuration'
            if 'layers' in config:
                return 'Configuration Downloaded'

    class Meta:
        verbose_name = "EPA Response"

    def __str__(self):
        return self.name


class FacilityType(models.Model):
    facility_type = models.CharField(max_length=50, help_text='Facility Type', blank=True, null=True)
    fac_code = models.CharField(max_length=5, help_text='Facility Code', blank=True, null=True, verbose_name='Fac Code')
    category = models.ForeignKey('Category', on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return self.facility_type


# todo: more like default config of logic.. rename?
# todo: allow matching of these to fields in the actual data set
class Category(LookupAbstract):
    media = models.ForeignKey('Media', on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


# todo: more closely link this with survey123.  Maybe allow input of the cross walk so its configurable and dynamic
class Survey123FieldType(LookupAbstract):
    field_type = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Survey123 Field Type"


class Unit(LookupAbstract):
    pass


class ESRIFieldTypes(models.Model):
    field_type = models.CharField(max_length=250)
    data_type = models.CharField(max_length=250)

    def __str__(self):
        return self.field_type


class MasterQuestion(models.Model):
    question = models.TextField(max_length=1000)
    # related_question = models.ManyToManyField('self', blank=True)

    # todo: why is media here and in category
    media = models.ForeignKey('Media', on_delete=models.PROTECT)
    category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, blank=True,
                                 help_text='Leaving category type empty will apply the question to ALL category types.')
    facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT, null=True, blank=True,
                                      help_text='Leaving facility type empty will apply the question to ALL facility types.')
    survey123_field_type = models.ForeignKey('Survey123FieldType', on_delete=models.PROTECT, null=True, blank=True,
                                             verbose_name='Survey123 Field Type')
    lookup = models.ForeignKey('LookupGroup', on_delete=models.PROTECT, null=True, blank=True,
                               verbose_name='Answer Type')
    # todo: triggers creation of second field for survey generation if not none
    default_unit = models.ForeignKey('Lookup', on_delete=models.PROTECT, null=True, blank=True,
                                     help_text='To generate a list of default values, select desired answer type and click "Save and Continue Editing"')
    related_questions = models.ManyToManyField('self', related_name='related_question', through='RelatedQuestionList',
                                               symmetrical=False)

    unique_id = models.UUIDField(default=uuid.uuid4())

    # todo: does question active make sense in here or just in the survey itself?
    # question_active = models.BooleanField(default=True)

    # sort_order = models.IntegerField(null=True, blank=True)

    # todo: add question hint
    # todo: is anything or everything required

    def __str__(self):
        return f"{self.question} ({self.media.label})"

    @property
    def formatted_survey_field_type(self):
        if self.survey123_field_type.field_type == 'select_one':
            return f"{self.survey123_field_type.field_type} {self.lookup.formatted_survey_name}"
        # could add more here but nothing useful I can see right now
        # values = {'list_name': self.lookup.formatted_survey_name}
        # return self.survey123_field_type.field_type.format(**values)
        return self.survey123_field_type.field_type

    @property
    def formatted_survey_field_name(self):
        name = re.sub(r'[^a-zA-Z\d\s:]', '', self.question.lower()).replace(" ", "_")
        unique_name = name[:110] + self.unique_id.hex[0:8]
        return unique_name

    # def formatted_survey_relevant_questions(self, layer_id):
    #     for r in RelatedQuestionList.objects.filter(related_id__pk=self.id):
    #         if r is not None:
    #             print(r.related)
    #             return f"$selected(${r.question}, {r.relevant_field})"

    def formatted_survey_category_field_relevant(self, survey, layer_id):
        for r in RelatedQuestionList.objects.filter(related_id__pk=self.id):
            if r is not None:
                return f"${{layer_{layer_id}_media}}='{self.media.description}' and selected(${{{r.question.formatted_survey_field_name}}}, \"{r.relevant_field.label}\")"
            if r is not None and self.facility_type is not None and self.media is not None:
                return f"${{layer_{layer_id}_media}}='{self.media.description}' and ${{layer_{layer_id}_Fac_Type}}='{self.facility_type.fac_code}' and selected(${{{r.question.formatted_survey_field_name}}}, \"{r.relevant_field.label}\")"
        if self.facility_type is not None and self.media is not None and int(layer_id) != survey.epa_response.system_layer_id:
            return f"${{layer_{layer_id}_media}}='{self.media.description}' and ${{layer_{layer_id}_Fac_Type}}='{self.facility_type.fac_code}'"
        else:
            return f"${{layer_{layer_id}_media}}='{self.media.description}'"

    def relevant_for_feature(self, feature, survey):
        layer_id = survey.layer
        if self.facility_type is not None \
                and self.media is not None \
                and int(layer_id) != survey.epa_response.system_layer_id:
            return feature['attributes'][f'layer_{layer_id}_media'] == self.media.description and \
                feature['attributes'][f'layer_{layer_id}_Fac_Type'] == self.facility_type.fac_code

        return feature['attributes'][f'layer_{layer_id}_media'] == self.media.description

    # does not need to be in class
    def get_formatted_required(self, required):
        return "true" if required else "false"

    def get_formatted_question(self, survey, layer_index, required):
        # must always return a list
        if self.lookup is not None and self.survey123_field_type.field_type != 'select_one':
            return [
                {
                    'type': 'begin_group',
                    'name': self.formatted_survey_field_name,
                    'label': self.question,
                    'relevant': f" {self.formatted_survey_category_field_relevant(survey, layer_index)}",
                },
                {
                    'type': self.formatted_survey_field_type.lower(),
                    'name': f'{self.formatted_survey_field_name}_measure',
                    'label': 'Measure'
                },
                {
                    'type': f'select_one {self.lookup.formatted_survey_name.lower()}',
                    'name': f'{self.formatted_survey_field_name}_choices',
                    'label': self.lookup.description,
                    'default': getattr(self.default_unit, 'label', None)
                },
                {
                    'type': 'end group'
                }
            ]

        q = [{
            'type': self.formatted_survey_field_type.lower(),
            'name': self.formatted_survey_field_name,
            'label': self.question,
            'relevant': f"{self.formatted_survey_category_field_relevant(survey, layer_index)}",
            'required': f"{self.formatted_survey_category_field_relevant(survey, layer_index)} and {self.get_formatted_required(required)}",
        }]

        return q

    class Meta:
        verbose_name = 'Master Question'


class Survey(models.Model):
    name = models.CharField(max_length=250)
    # todo: determine how to select this and then make fields available for matching to category values
    # perhaps this is a url to a published service?
    # this way the data doesn't even need to be on same machine or network. could even be in agol
    survey123_service = models.URLField(null=True, blank=True)
    epa_response = models.ForeignKey('EPAResponse', on_delete=models.SET_NULL, null=True, blank=True,
                                     help_text='Select an active EPA response and click "Save and Continue Editing" before proceeding.')

    # the querying the service based on extent or values would be much more straight forward
    # todo: limit the results of the data source to only select a subset.  This is for creating preload survey

    # media = models.ForeignKey('Media', on_delete=models.PROTECT)
    # facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT)
    # sub_facility_type = models.ForeignKey('FacilitySubType', on_delete=models.PROTECT)

    selected_features = models.TextField(null=True, blank=True)
    layer = models.IntegerField(null=True, blank=True)  # Feature Layer to collect (system or facility)

    # color_code = models.CharField(max_length=6)

    def __str__(self):
        return self.name

    survey123_translation = {
        'name': 'formatted_survey_field_name',
        'label': 'question',
    }

    def survey_service_ready(self):
        if self.survey123_service is not None:
            return True
        return False

    survey_service_ready.boolean = True
    survey_service_ready.short_description = "Valid Survey123 Service"

    def base_service_ready(self):
        if self.epa_response is not None and self.epa_response.map_service_config is not None:
            return True
        return False

    base_service_ready.boolean = True
    base_service_ready.short_description = "Download Service Config"

    def get_assigned_questions(self):
        assigned_questions = []
        for qs in self.question_set.all():
            for q in qs.questionlist_set.filter(active=True).order_by('sort_order'):
                assigned_questions.append((q.question, self.layer, q.required))
                for related_q in q.question.relatedquestionlist_set.all():
                    if not self.question_set.filter(questions=related_q.related).exists():
                        assigned_questions.append((related_q.related, self.layer, True))

        return assigned_questions

    # returns the active records of relationship between questionset and actual question
    def format_questions(self, questions):
        formatted_questions = []
        for q, l, r in questions:
            formatted_questions += q.get_formatted_question(self, l, r)
        return formatted_questions
        #
        # assigned_questions = []
        # for qs in self.question_set.all():
        #     for q in qs.questionlist_set.filter(active=True).order_by('sort_order'):
        #         assigned_questions += q.question.get_formatted_question(self.layer, q.required)
        #         for related_q in q.question.relatedquestionlist_set.all():
        #             assigned_questions += related_q.related.get_formatted_question(self.layer, True)
        #
        # return assigned_questions

    def get_base_domains(self):
        config = json.loads(self.epa_response.map_service_config)
        domains = {}
        for l in config['layers']:
            for f in l['fields']:
                if f['domain'] is not None:
                    domains[f['domain']['name']] = f['domain']['codedValues']
        return domains

    def get_assigned_lookups(self, questions):
        q = [x[0] for x in questions]
        return [
            {
                'list_name': x.group.formatted_survey_name,
                'name': x.label,
                'label': x.description,
            } for x in Lookup.objects.filter(group__masterquestion__in=q).distinct()
        ]

    def generate_xlsform(self):
        template = os.path.join(settings.BASE_DIR, settings.XLS_FORM_TEMPLATE)
        output_survey = os.path.join(settings.BASE_DIR, f'QuestionLibrary\\generated_forms\\{self.id}.xlsx')
        shutil.copy(template, output_survey)
        orig_survey_df = pd.read_excel(output_survey, sheet_name='survey')
        orig_choices_df = pd.read_excel(output_survey, sheet_name='choices')

        # assigned_questions = MasterQuestion.objects.filter(question_set__surveys=self)
        # feat_service = json.loads(self.epa_response.map_service_config)
        # fields = self.get_formatted_fields()

        # fields =[]
        # for x in fields:

        if self.layer == self.epa_response.system_layer_id:
            # system (base inventory) layer
            fields = self.get_formatted_survey_fields(self.layer)
        else:
            # feature layer
            fields = self.get_formatted_fields()

        field_df = pd.DataFrame(fields)
        field_df_drop_dups = field_df.drop_duplicates()

        if self.layer == self.epa_response.system_layer_id:
            layer = [{
                'form_title': self.name,
                'form_id': '',
                'instance_name': 'concat("System Name: "+${layer_'+str(self.layer)+'_SystemName}, " ", "System Status: " + ${layer_'+str(self.layer)+'_ActivityStatus})',
                'style': 'theme-grid'
            }]
        else:
            layer = [{
                'form_title': self.name,
                'form_id': '',
                'instance_name': 'concat("Facility Name: "+${layer_'+str(self.layer)+'_FacilityName}, " ", "Facility ID: " + ${layer_'+str(self.layer)+'_FacilityID}, " ", "Facility Type: " + ${layer_'+str(self.layer)+'_Fac_Type})',
                'style': 'theme-grid'
            }]

        settings_df = pd.DataFrame(layer)
        # add survey status and geopoint fields to the survey. Not sure if this is the best way to do this. works for now.
        survey_status = [{
            'type': 'hidden',
            'name': 'survey_status',
            'label': 'Survey Status'}]
        status_df = pd.DataFrame(survey_status)

        geopoint = [{
            'type': 'geopoint',
            'name': 'geometry',
            'label': 'Edit Geometry'}]
        geopoint_df = pd.DataFrame(geopoint)

        questions = self.get_assigned_questions()
        formatted_questions = self.format_questions(questions)
        questions_df = pd.DataFrame(formatted_questions)
        # all_questions_df = [questions_df, status_df]
        survey_df_all = [field_df, questions_df, status_df, geopoint_df]
        survey_df = orig_survey_df.append(survey_df_all)

        choices = self.get_assigned_lookups(questions)

        # this should grab domains from base service
        fs_domains = self.get_base_domains()
        fs_choices = []
        for name, values in fs_domains.items():
            fs_choices += [
                {
                    'list_name': name,
                    'name': v['code'],
                    'label': v['name']
                } for v in values
            ]
        lookups_df = pd.DataFrame(choices)
        fs_lookups_df = pd.DataFrame(fs_choices)
        lookups_all = [lookups_df, fs_lookups_df]
        choices_df = orig_choices_df.append(lookups_all)

        with pd.ExcelWriter(output_survey, mode='w') as writer:
            survey_df.to_excel(writer, sheet_name='survey', index=False)
            choices_df.to_excel(writer, sheet_name='choices', index=False)
            settings_df.to_excel(writer, sheet_name='settings', index=False)
        # return questions_df, choices_df

    # returns type and appearance
    def get_base_feature_field_info(self, field):
        if field['domain'] is not None:
            appearance = "" if len(field['domain']['codedValues']) < 5 else "autocomplete"
            return f"select_one {field['domain']['name']}", appearance
        return ESRIFieldTypes.objects.get(field_type=field['type']).data_type, ""

    def get_formatted_fields(self):
        feat_service = json.loads(self.epa_response.map_service_config)['layers']
        survey_fields = []
        omit_fields = {'created_user', 'created_date', 'AlternateTextID',
                       'last_edited_user', 'last_edited_date', 'OBJECTID'}

        # todo do these need to be hidden or do the need to be left out completely
        # todo need to figure out a way to not include the base facility inventory fields when the user is doing a base inventory assessment

        for layer in feat_service:
            # system layer
            # if layer['name'] == 'Base_Inventory':
            if layer['id'] == self.epa_response.system_layer_id:
                survey_fields.append({'type': 'begin group',
                                      'name': 'sys_info',
                                      'label': '<h2 style="background-color:#3295F7; text-align:center;">System Name: ${layer_' + str(layer['id']) + '_SystemName} System ID ${layer_' + str(layer['id']) + '_pws_fac_id}</h2>',
                                      'appearance': 'w1 field-list'})
                for field in layer['fields']:
                    if field['type'] == 'esriFieldTypeGUID' or field['type'] == 'esriFieldTypeOID':
                        survey_fields.append({
                            'type': 'hidden',
                            'name': formattedFieldName(layer['id'], field['name']),
                            'label': field['alias'],
                            'readonly': 'yes'
                        })
                    elif field['name'] not in omit_fields:
                        t, appearance = self.get_base_feature_field_info(field)
                        survey_fields.append({
                            'type': t,
                            'name': formattedFieldName(layer['id'], field['name']),
                            'label': field['alias'],
                            'appearance': appearance,
                            'readonly': 'yes'  # todo: figure out if system should ever be collected on the fly...
                        })
                survey_fields.append({'type': 'end group'})
            # facility layer
            # elif layer['name'] == 'Base_Facility_Inventory':
            elif layer['id'] == self.epa_response.facility_layer_id:
                survey_fields.append({'type': 'begin group',
                                      'name': 'facility_info',
                                      'label': '<h2 style="background-color:#00C52A; text-align:center;">Facility Name: ${layer_' + str(layer['id']) + '_FacilityName} Facility ID: ${layer_' + str(layer['id']) + '_FacilityID}</h2>',
                                      'appearance': 'w1 field-list'})
                for field in layer['fields']:
                    if field['type'] == 'esriFieldTypeGUID' or field['type'] == 'esriFieldTypeOID':
                        survey_fields.append({
                            'type': 'hidden',
                            'name': formattedFieldName(layer['id'], field['name']),
                            'label': field['alias'],
                            'readonly': 'yes'
                        })
                    elif field['name'] not in omit_fields:
                        t, appearance = self.get_base_feature_field_info(field)
                        survey_fields.append({
                            'type': t,
                            'name': formattedFieldName(layer['id'], field['name']),
                            'label': field['alias'],
                            'appearance': appearance,
                            'readonly': 'pulldata("@property", "mode") = "edit"'
                        })
                survey_fields.append({'type': 'end group'})

        return survey_fields

    def get_formatted_survey_fields(self, layer_id):
        feat_service = json.loads(self.epa_response.map_service_config)['layers']
        survey_fields = [{'type': 'begin group',
                          'name': 'sys_info',
                          'label': '<h2 style="background-color:#3295F7; text-align:center;">System Name: ${layer_' + str(layer_id) + '_SystemName} System ID: ${layer_' + str(layer_id) + '_pws_fac_id}</h2>',
                          'appearance': 'w1 field-list'}]

        omit_fields = {'created_user', 'created_date', 'AlternateTextID',
                       'last_edited_user', 'last_edited_date', 'OBJECTID'}

        for layer in feat_service:
            if layer['id'] == int(layer_id):
                for field in layer['fields']:
                    if field['name'] not in omit_fields:
                        survey_fields.append(
                            {'type': 'text' if field['domain'] is None else f'select_one {field["domain"]["name"]}',
                             'name': formattedFieldName(layer['id'], field['name']),
                             'label': field['alias'],
                             'readonly': 'yes'
                             },
                        )
                survey_fields.append({'type': 'end group'})
        return survey_fields

    class Meta:
        verbose_name = "Assessment"


# todo: figure out how to publish survey123. it might have to be manual


class QuestionSet(models.Model):
    name = models.CharField(max_length=250)
    owner = models.CharField(max_length=250)
    surveys = models.ManyToManyField('Survey', related_name='question_set')
    questions = models.ManyToManyField('MasterQuestion', related_name='question_set', through='QuestionList')
    sort_order = models.IntegerField(null=True, blank=True)

    # media = models.ForeignKey('Media', on_delete=models.PROTECT, null=True, blank=True)
    # category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, blank=True)
    # facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.name

    # todo: change the surveys many to many field back to a relationship table


class QuestionList(models.Model):
    set = models.ForeignKey('QuestionSet', on_delete=models.PROTECT)
    question = models.ForeignKey('MasterQuestion', on_delete=models.PROTECT)
    active = models.BooleanField(default=True)
    required = models.BooleanField(default=True)
    sort_order = models.IntegerField(null=True, blank=True)


class SurveyResponse(models.Model):
    response = models.TextField(null=True, blank=True)


#
# class RelatedQuestion(models.Model):
#     questions = models.ManyToManyField('MasterQuestion', related_name='related_questions', through='RelatedQuestionList')
#     # answer = models.IntegerField(null=True, blank=True)

class RelatedQuestionList(models.Model):
    related = models.ForeignKey('MasterQuestion', on_delete=models.PROTECT, related_name='master_questions')
    question = models.ForeignKey('MasterQuestion', on_delete=models.PROTECT)
    relevant_field = models.ForeignKey('Lookup', on_delete=models.PROTECT, null=True, blank=True)


class Dashboard(models.Model):
    name = models.CharField(max_length=500)
    draft_id = models.UUIDField()
    production_id = models.UUIDField()
    base_feature_service = models.URLField()
    draft_service_view = models.URLField()
    production_service_view = models.URLField()

    def __str__(self):
        return self.name

    @property
    def view_draft(self):
        return mark_safe(f'<a target="_blank" href="https://www.arcgis.com/apps/dashboards/{self.draft_id.hex}">View {self.name} Draft</a>')

    @property
    def view_production(self):
        return mark_safe(f'<a target="_blank" href="https://www.arcgis.com/apps/dashboards/{self.production_id.hex}">View {self.name} Production</a>')
