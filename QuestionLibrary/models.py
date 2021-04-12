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
from urllib.parse import urlencode
from itertools import islice
from django.core.exceptions import ValidationError
import csv
from django.utils.html import format_html


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
    pass

    class Meta:
        verbose_name = "Response Type"


class Lookup(LookupAbstract):
    group = models.ForeignKey('LookupGroup', on_delete=models.CASCADE, related_name='lookups')


class Media(LookupAbstract):
    pass
    # class Meta:
    #     verbose_name = '1. Media'


# # todo: if this is to be more generic then Water should not be used here... SubType perhaps is better?
# class FacilitySubType(LookupAbstract):
#     pass


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

    # facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT)
    # sub_facility_type = models.ForeignKey('FacilitySubType', on_delete=models.PROTECT)
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


# todo: more closely link this with survey123.  Maybe allow input of the cross walk so its configurable and dynamic

class ResponseType(LookupAbstract):
    pass

    survey123_field_type = models.CharField(max_length=50)

    class Meta:
        verbose_name = "ESRI Response Type"


class Unit(LookupAbstract):
    pass


class FeatureServiceResponse(models.Model):
    fs_response_type = models.CharField(max_length=250)
    esri_field_type = models.CharField(max_length=250)

    def __str__(self):
        return self.fs_response_type


class MasterQuestion(models.Model):
    question = models.TextField(max_length=1000)
    # related_question = models.ManyToManyField('self', blank=True)

    # todo: why is media here and in category
    media = models.ForeignKey('Media', on_delete=models.PROTECT)
    category = models.ForeignKey('Category', on_delete=models.PROTECT, null=True, blank=True)
    facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT, null=True, blank=True)
    response_type = models.ForeignKey('ResponseType', on_delete=models.PROTECT, verbose_name='Survey123 Field Type')
    lookup = models.ForeignKey('LookupGroup', on_delete=models.PROTECT, null=True, blank=True,
                               verbose_name='Response Type')
    # todo: triggers creation of second field for survey generation if not none
    default_unit = models.ForeignKey('Lookup', on_delete=models.PROTECT, null=True, blank=True,
                                     help_text='To generate a list of default values, select desired response type and click "Save and Continue Editing"')
    related_questions = models.ManyToManyField('self', related_name='related_question', through='RelatedQuestionList',
                                               symmetrical=False)

    # todo: does question active make sense in here or just in the survey itself?
    # question_active = models.BooleanField(default=True)

    # sort_order = models.IntegerField(null=True, blank=True)

    # todo: add question hint
    # todo: is anything or everything required

    def __str__(self):
        return f"{self.question} ({self.media.label})"

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

    # def formatted_survey_relevant_questions(self, layer_id):
    #     for r in RelatedQuestionList.objects.filter(related_id__pk=self.id):
    #         if r is not None:
    #             print(r.related)
    #             return f"$selected(${r.question}, {r.relevant_field})"

    def formatted_survey_category_field_relevant(self, layer_id):
        for r in RelatedQuestionList.objects.filter(related_id__pk=self.id):
            if r is not None:
                return f"${{layer_{layer_id}_media}}='{self.media.description}' and selected(${{{r.question.formatted_survey_field_name}}}, \"{r.relevant_field.label}\")"
            if r is not None and self.facility_type is not None and self.media is not None:
                return f"${{layer_{layer_id}_media}}='{self.media.description}' and ${{layer_{layer_id}_Fac_Type}}='{self.facility_type.fac_code}' and selected(${{{r.question.formatted_survey_field_name}}}, \"{r.relevant_field.label}\")"
        if self.facility_type is not None and self.media is not None:
            return f"${{layer_{layer_id}_media}}='{self.media.description}' and ${{layer_{layer_id}_Fac_Type}}='{self.facility_type.fac_code}'"
        else:
            return f"${{layer_{layer_id}_media}}='{self.media.description}'"

    def relevant_for_feature(self, feature, layer_id):
        if self.facility_type is not None and self.media is not None and layer_id != 0:
            return feature['attributes'][f'layer_{layer_id}_media'] == self.media.description and \
                   feature['attributes'][f'layer_{layer_id}_Fac_Type'] == self.facility_type.fac_code

        return feature['attributes'][f'layer_{layer_id}_media'] == self.media.description

    def get_formatted_question(self, layer_index):
        # must always return a list
        if self.lookup is not None and self.response_type.survey123_field_type != 'select_one':
            return [{
                'type': 'begin_group',
                'name': self.formatted_survey_field_name,
                'label': self.question,
                'relevant': f" {self.formatted_survey_category_field_relevant(layer_index)}",
            },
                {
                    'type': self.formatted_survey_field_type.lower(),
                    'name': f'{self.formatted_survey_field_name}_measure',
                    'label': 'Measure'
                },
                {
                    'type': f'select_one {self.lookup.label.lower()}',
                    'name': f'{self.formatted_survey_field_name}_choices',
                    'label': self.lookup.description,
                    'default': getattr(self.default_unit, 'label', None)
                },
                {
                    'type': 'end group'
                }

            ]

        return [{
            'type': self.formatted_survey_field_type.lower(),
            'name': self.formatted_survey_field_name,
            'label': self.question,
            'relevant': f"{self.formatted_survey_category_field_relevant(layer_index)}",
            'required': f"{self.formatted_survey_category_field_relevant(layer_index)}",
        }]

    class Meta:
        verbose_name = 'Master Question'


class Survey(models.Model):
    name = models.CharField(max_length=250)
    # todo: determine how to select this and then make fields available for matching to category values
    # perhaps this is a url to a published service?
    # this way the data doesn't even need to be on same machine or network. could even be in agol
    base_map_service = models.URLField()
    survey123_service = models.URLField(null=True, blank=True)

    # the querying the service based on extent or values would be much more straight forward
    # todo: limit the results of the data source to only select a subset.  This is for creating preload survey

    # store the fields from the service locally for reference in forms?
    service_config = models.TextField(null=True, blank=True)

    # media = models.ForeignKey('Media', on_delete=models.PROTECT)
    # facility_type = models.ForeignKey('FacilityType', on_delete=models.PROTECT)
    # sub_facility_type = models.ForeignKey('FacilitySubType', on_delete=models.PROTECT)

    selected_features = models.TextField(null=True, blank=True)
    layer = models.TextField(null=True, blank=True)
    assessment_layer = models.TextField(null=True, blank=True)

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
        if self.base_map_service is not None:
            return True
        return False

    base_service_ready.boolean = True
    base_service_ready.short_description = "Download Service Config"

    def generate_xlsform(self):
        template = os.path.join(settings.BASE_DIR, settings.XLS_FORM_TEMPLATE)
        output_survey = os.path.join(settings.BASE_DIR, f'QuestionLibrary\\generated_forms\\{self.id}.xlsx')
        shutil.copy(template, output_survey)
        orig_survey_df = pd.read_excel(output_survey, sheet_name='survey')
        orig_choices_df = pd.read_excel(output_survey, sheet_name='choices')
        assigned_questions = MasterQuestion.objects.filter(question_set__surveys=self)
        feat_service = json.loads(self.service_config)
        # fields = self.get_formatted_fields()

        # fields =[]
        # for x in fields:

        if self.layer == '0':
            fields = self.get_formatted_survey_fields(self.layer)
        else:
            fields = self.get_formatted_fields()

        field_df = pd.DataFrame(fields)
        field_df_drop_dups = field_df.drop_duplicates()

        layer = [{
            'form_title': self.name,
            'form_id': '',
            'instance_name': 'concat("System Name: "+${layer_0_SystemName}, " ", "System Status: " + ${layer_0_ActivityStatus})',

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

        questions = []
        for x in assigned_questions:
            questions.extend(x.get_formatted_question(self.layer))
        questions_df = pd.DataFrame(questions)
        # all_questions_df = [questions_df, status_df]
        survey_df_all = [questions_df, field_df, status_df, geopoint_df]
        survey_df = orig_survey_df.append(survey_df_all)

        assigned_lookups = Lookup.objects.filter(group__masterquestion__question_set__surveys=self).distinct()
        choices = [
            {
                'list_name': x.group.formatted_survey_name,
                'name': x.label,
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
            settings_df.to_excel(writer, sheet_name='settings', index=False)
        # return questions_df, choices_df

    def formattedFieldName(self, layer_id, field_name):
        return f"layer_{layer_id}_{field_name}"

    def getLayers(self, service, user):
        layers = []
        tables = []
        social = user.social_auth.get(provider='agol')
        token = social.get_access_token(load_strategy())
        r = requests.get(url=service, params={'token': token, 'f': 'json'})
        for x in r.json()['layers']:
            q = requests.get(url=service + '/' + str(x['id']), params={'token': token, 'f': 'json'})
            layers.append(q.json())
        for x in r.json()['tables']:
            q = requests.get(url=service + '/' + str(x['id']), params={'token': token, 'f': 'json'})
            tables.append(q.json())

        self.service_config = json.dumps({"layers": layers, "tables": tables})

    def getMapService(self, user):
        if not self.service_config:
            self.getLayers(user=user, service=self.base_map_service)

    def getSurveyService(self, user):
        self.getLayers(user=user, service=self.survey123_service)

    def getBaseAttributes(self, user):
        features = []
        social = user.social_auth.get(provider='agol')
        token = social.get_access_token(load_strategy())
        # r = requests.get(url=self.base_map_service, params={'token': token, 'f': 'json'})

        service_config_layers = json.loads(self.service_config)['layers']
        # get layers that serve a origin in relationship
        # origin_layers = [x for x in service_config_layers if
        #                  x['id'] = self.layer]
        # any(y['role'] == 'esriRelRoleOrigin' for y in x['relationships'])] #service config for the selected layer x=origin_id?

        for x in service_config_layers:
            if x['id'] == int(self.layer):
                origin_layer = x

                result_offset = 0
                related_responses = {}
                selected = self.selected_features.split(',')

                object_ids = selected

                if len(object_ids) == 0:
                    break
                else:
                    result_offset += 10
                    # get features in origin layer

                p = {"where": "1=1",
                     "objectIds": ','.join(object_ids),
                     # "resultOffset": result_offset,
                     # "resultRecordCount": 10,
                     "outFields": "*",
                     'token': token,
                     'f': 'json'}

                params = '&'.join([f'{k}={v}' for k, v in p.items()])

                q = requests.get(url=self.base_map_service + '/' + str(self.layer) + '/query',
                                 params=params)
                layer_name = origin_layer['name']

                # object_ids = [str(z['attributes']['OBJECTID']) for z in q.json()['features']]

                # get the related layer
                # todo: figure out where to pull geometry from... like froms base_facility_inventory... not the origin table
                for related_layer in [y for y in origin_layer['relationships']]:  # esriRelRoleDestination
                    p = {"objectIds": ','.join(object_ids),
                         "relationshipId": related_layer['id'],
                         "outFields": "*",
                         'token': token,
                         'f': 'json'}
                    params = '&'.join([f'{k}={v}' for k, v in p.items()])
                    related_responses[related_layer['id']] = requests.get(
                        url=self.base_map_service + '/' + str(self.layer) + '/queryRelatedRecords',
                        params=params)

                    # deconstruct the queryRelatedRecords response for easier handling since we only have 1 objectid at a time
                for origin_feature in q.json()['features']:
                    # loop through relationships to get all features in all related layers
                    feature = {'attributes': {}, 'geometry': origin_feature.get('geometry', None)}

                    for k, v in origin_feature['attributes'].items():
                        feature['attributes'][self.formattedFieldName(x['id'], k)] = v

                    for related_layer_id, related_response in related_responses.items():
                        related_features = [z['relatedRecords'][0] for z in
                                            related_response.json()['relatedRecordGroups']
                                            if z['objectId'] == origin_feature['attributes']['OBJECTID']]
                        for related_feature in related_features:

                            # this is fair dynamic but geometry needs to be captured correctly
                            # this should work correctly based on our current understanding of how the data is structured and fall back to
                            # the origin geometry if related records isn't the for some reason
                            if feature.get('geometry', None) is None:
                                feature['geometry'] = related_feature.get('geometry', None)

                            for k, v in related_feature['attributes'].items():
                                feature['attributes'][self.formattedFieldName(related_layer_id, k)] = v

                    # set default values for survey123 questions for existing features from base data
                    for question_set in self.question_set.all():
                        for question in question_set.questions.all():
                            if question.relevant_for_feature(feature, self.layer) and question.default_unit is not None:
                                feature['attributes'][
                                    f'{question.formatted_survey_field_name}_choices'] = question.default_unit.description

                    features.append(feature)
                    print(feature)

                # print(features)
        return features

    def postAttributes(self, user):
        social = user.social_auth.get(provider='agol')
        token = social.get_access_token(load_strategy())
        feat = self.getBaseAttributes(user)
        data = urlencode({"adds": json.dumps(feat)})

        r = requests.post(url=self.survey123_service + '/0/applyEdits', params={'token': token, 'f': 'json'},
                          data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
        print(r)

    def get_formatted_fields(self):
        feat_service = json.loads(self.service_config)['layers']
        fields = []
        omit_fields = {'created_user', 'created_date', 'AlternateTextID',
                       'last_edited_user', 'last_edited_date', 'OBJECTID'}

        # todo do these need to be hidden or do the need to be left out completely
        # todo need to figure out a way to not include the base facility inventory fields when the user is doing a base inventory assessment

        for x in feat_service:
            if x['name'] == 'Base Inventory':
                fields.append({'type': 'begin group',
                   'name': 'sys_info',
                   'label': '<h2 style="background-color:#3295F7;"><center>${layer_0_SystemName}</h2></center>',
                   'apperance': 'w8 field-list'})
                for y in x['fields']:
                    if y['type'] == 'esriFieldTypeGUID' or y['type'] == 'esriFieldTypeOID':
                        fields.append({
                            'type': 'hidden',
                            'name': self.formattedFieldName(x['id'], y['name']),
                            'label': y['alias'],
                            'readonly': 'yes'
                        })
                    elif y['name'] not in omit_fields:
                        fields.append({
                            'type': FeatureServiceResponse.objects.get(fs_response_type=y['type']).esri_field_type,
                            'name': self.formattedFieldName(x['id'], y['name']),
                            'label': y['alias'],
                            'readonly': 'yes'
                        })
                fields.append({'type': 'end group'})
            elif x['name'] == 'Base Facility Inventory':
                fields.append({'type': 'begin group',
                   'name': 'facility_info',
                   'label': '<h2 style="background-color:#00C52A;"><center>${layer_1_FacilityName}</h2></center>',
                   'apperance': 'w8 field-list'})
                for y in x['fields']:
                    if y['type'] == 'esriFieldTypeGUID' or y['type'] == 'esriFieldTypeOID':
                        fields.append({
                            'type': 'hidden',
                            'name': self.formattedFieldName(x['id'], y['name']),
                            'label': y['alias'],
                            'readonly': 'yes'
                        })
                    elif y['name'] not in omit_fields:
                        fields.append({
                            'type': FeatureServiceResponse.objects.get(fs_response_type=y['type']).esri_field_type,
                            'name': self.formattedFieldName(x['id'], y['name']),
                            'label': y['alias'],
                            'readonly': 'yes'
                        })
                fields.append({'type':'end group'})

        #     for y in x['fields']:
        #         if y['name'] not in omit_fields:
        #             fields.append({
        #                 'type': 'text',
        #                 'name': self.formattedFieldName(x['id'], y['name']),
        #                 'label': y['alias'],
        #                 'readonly': 'yes'
        #             })
        # else:
        #     for y in x['fields']:
        #         if y['type'] == 'esriFieldTypeGUID' or y['type'] == 'esriFieldTypeOID':
        #             fields.append({
        #                 'type': 'hidden',
        #                 'name': self.formattedFieldName(x['id'], y['name']),
        #                 'label': y['alias'],
        #                 'readonly': 'yes'
        #             })
        #         else:
        #             fields.append({
        #                 'type': FeatureServiceResponse.objects.get(fs_response_type=y['type']).esri_field_type,
        #                 'name': self.formattedFieldName(x['id'], y['name']),
        #                 'label': y['alias'],
        #                 'readonly': 'yes'
        #             })
        #         fields.append({'type': 'end group'})
        return fields

    def get_formatted_survey_fields(self, layer_id):
        feat_service = json.loads(self.service_config)['layers']
        fields = [{'type': 'begin group',
                   'name': 'sys_info',
                   'label': '<h2 style="background-color:#3295F7;"><center>System Information</h2></center>',
                   'apperance': 'w8 field-list'}]

        omit_fields = {'created_user', 'created_date', 'AlternateTextID',
                       'last_edited_user', 'last_edited_date', 'OBJECTID'}

        for x in feat_service:
            if x['id'] == int(layer_id):
                for y in x['fields']:
                    if y['name'] not in omit_fields:
                        fields.append(
                            {'type': 'text',
                             'name': self.formattedFieldName(x['id'], y['name']),
                             'label': y['alias'],
                             'readonly': 'yes'
                             },
                        )
            fields.append({'type':'end group'})
        return fields

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
