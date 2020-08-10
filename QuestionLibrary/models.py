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
    def formatted_survey_category_field_relevant(self):
        return f"${{base_facility_inventory_Fac_Type}}='{self.category.facility_type.label}'"

    @property
    def formatted_survey_media_field_relevant(self):
        return f"${{base_inventory_media}}='{self.media.label}'"

    # @property
    # def formatted_survey_bwn_date_field_relevant(self):
    #     if self.question == "On what date was the BWN issued?":
    #         return
    #     return f"${{boil_water_notice}}='yes'"
    #
    # @property
    # def formatted_survey_bwn_redacted_field_relevant(self):
    #     if self.question == "On what date was the BWN redacted?":
    #         return
    #     return f"${{boil_water_notice}}='yes'"



    def get_formatted_question(self):
        # must always return a list
        if self.lookup is not None and self.response_type.survey123_field_type != 'select_one':
            return [{
                'type': 'begin_group',
                'name': self.formatted_survey_field_name,
                'label': self.question,
                'relevant': f"{self.formatted_survey_media_field_relevant} and {self.formatted_survey_category_field_relevant}",
            },
                {
                    'type': self.formatted_survey_field_type,
                    'name': f'{self.formatted_survey_field_name}_measure',
                    'label': 'Measure'
                },
                {
                    'type': f'select_one {self.lookup.label}',
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
            'relevant': f"{self.formatted_survey_media_field_relevant} and {self.formatted_survey_category_field_relevant}",
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
        fields = self.get_formatted_fields()

        field_df = pd.DataFrame(fields)
        field_df_drop_dups = field_df.drop_duplicates()

        questions = []
        for x in assigned_questions:
            questions.extend(x.get_formatted_question())

        questions_df = pd.DataFrame(questions)
        survey_df_all = [questions_df, field_df_drop_dups]
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

    def formattedFieldName(self, layer_name, field_name):
        return f"{layer_name.lower().replace(' ', '_')}_{field_name}"

    def getLayers(self, service, user):
        layers = []
        social = user.social_auth.get(provider='agol')
        token = social.get_access_token(load_strategy())
        r = requests.get(url=service, params={'token': token, 'f': 'json'})
        for x in r.json()['layers']:
            q = requests.get(url=service + '/' + str(x['id']), params={'token': token, 'f': 'json'})
            layers.append(q.json())

        self.service_config = json.dumps(layers)

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

        service_config_layers = json.loads(self.service_config)
        # get layers that serve a origin in relationship
        origin_layers = [x for x in service_config_layers if
                         any(y['role'] == 'esriRelRoleOrigin' for y in x['relationships'])]
        for x in origin_layers:
            # count = requests.get(url=self.base_map_service + '/' + str(x['id']) + '/query',
            #                      params={"where": "1=1", "outFields": "*", "returnCountOnly": "true", 'token': token,
            #                              'f': 'json'})

            result_offset = 0
            related_responses = {}
            while True:
                # get features in origin layer
                q = requests.get(url=self.base_map_service + '/' + str(x['id']) + '/query',
                                 params={"where": "1=1",
                                         "resultOffset": result_offset,
                                         "resultRecordCount": 10,
                                         "outFields": "*",
                                         'token': token,
                                         'f': 'json'})
                layer_name = x['name']

                object_ids = [str(z['attributes']['OBJECTID']) for z in q.json()['features']]
                if len(object_ids)==0:
                    break
                else:
                    result_offset+=10

                for related_layer in [y for y in x['relationships'] if y['role'] == 'esriRelRoleOrigin']:
                    related_responses[related_layer['name']] = requests.get(
                        url=self.base_map_service + '/' + str(x['id']) + '/queryRelatedRecords',
                        params={"objectIds": ','.join(object_ids),
                                "relationshipId": related_layer['id'],
                                "outFields": "*",
                                'token': token,
                                'f': 'json'})

                    # deconstruct the queryRelatedRecords response for easier handling since we only have 1 objectid at a time

                for origin_feature in q.json()['features']:
                # loop through relationships to get all features in all related layers
                    for related_layer_name, related_response in related_responses.items():
                        related_features = [z['relatedRecords'][0] for z in related_response.json()['relatedRecordGroups']
                                            if z['objectId'] == origin_feature['attributes']['OBJECTID']]
                        for related_feature in related_features:
                            # todo: figure out where to pull geometry from... like froms base_facility_inventory... not the origin table
                            # this is fair dynamic but geometry needs to be captured correctly
                            # this should work correctly based on our current understanding of how the data is structured and fall back to
                            # the origin geometry if related records isn't the for some reason
                            feature = {'attributes': {}, 'geometry': origin_feature.get('geometry', related_feature.get('geometry', None))}

                            for k, v in related_feature['attributes'].items():
                                feature['attributes'][self.formattedFieldName(related_layer_name, k)] = v

                            for k, v in origin_feature['attributes'].items():
                                feature['attributes'][self.formattedFieldName(layer_name, k)] = v

                            features.append(feature)
                            print(feature)
        print(features)
        return features

    def postAttributes(self, user):
        social = user.social_auth.get(provider='agol')
        token = social.get_access_token(load_strategy())
        feat = self.getBaseAttributes(user)
        data = urlencode({"adds": json.dumps(feat)})
        r = requests.post(url=self.survey123_service + '/0/applyEdits', params={'token': token, 'f': 'json'},
                          data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})


    def get_formatted_fields(self):
        feat_service = json.loads(self.service_config)
        fields = []
        omit_fields ={'FACID', 'FACdetailID' 'created_user', 'created_date',
                       'AlternateTextID', 'SystemTextIDPublic', 'FederalSystemType',
                       'last_edited_user', 'last_edited_user'}
        #todo do these need to be hidden or do the need to be left out completely


        for x in feat_service:
            for y in x['fields']:
                if y['type'] == 'esriFieldTypeGUID' or y['type'] == 'esriFieldTypeOID':
                    fields.append({
                        'type': 'hidden',
                        'name': self.formattedFieldName(x['name'], y['name']),
                        'label': y['alias'],
                        'bind::esri:fieldType': 'esriFieldTypeInteger'
                    })
                elif y['name'] in omit_fields:
                    fields.append({
                        'type': 'hidden',
                        'name': self.formattedFieldName(x['name'], y['name']),
                        'label': y['alias'],
                        'bind::esri:fieldType': 'esriFieldTypeInteger'
                    })
                else:
                    fields.append({
                        'type': FeatureServiceResponse.objects.get(fs_response_type=y['type']).esri_field_type,
                        'name': self.formattedFieldName(x['name'], y['name']),
                        'label': y['alias']
                    })

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
