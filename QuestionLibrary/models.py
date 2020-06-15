from django.db import models
from django.conf import settings
import shutil
import pandas as pd
import os
import re

# todo: move to model
responses = (
    ('yes', 'Yes/No'),
    ('no', 'Memo'),
    ('maybe', 'Integer'),
    ('maybe', 'Double'),
    ('maybe', 'Integer/Lookup'),
    ('maybe', 'Notes'),
)


class LookupAbstract(models.Model):
    label = models.CharField(max_length=50)
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


class MasterQuestion(models.Model):
    question = models.TextField(max_length=1000)

    # todo: why is media here and in category
    media = models.ForeignKey('Media', on_delete=models.PROTECT)
    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    response_type = models.ForeignKey('ResponseType', on_delete=models.PROTECT)

    # todo: triggers creation of second field for survey generation if not none
    units = models.ForeignKey('Unit', on_delete=models.PROTECT, null=True, blank=True)

    # todo: make required if response_type is lookup
    lookup = models.ForeignKey('LookupGroup', on_delete=models.PROTECT, null=True, blank=True)

    # todo: does question active make sense in here or just in the survey itself?
    question_active = models.BooleanField(default=True)

    sort_order = models.IntegerField(null=True, blank=True)

    # todo: add question hint
    # todo: is anything or everything required

    @property
    def formatted_survey_field_type(self):
        if self.lookup is not None:
            return f"{self.response_type.survey123_field_type} {self.lookup.formatted_survey_name}"
        # could add more here but nothing useful I can see right now
        # values = {'list_name': self.lookup.formatted_survey_name}
        # return self.response_type.survey123_field_type.format(**values)
        return self.response_type.survey123_field_type

    def __str__(self):
        return self.question

    @property
    def formatted_survey_field_name(self):
        return re.sub(r'[^a-zA-Z\d\s:]', '', self.question.lower()).replace(" ", "_")

    @property
    def formatted_survey_field_relevant(self):
        return f"${{media}}='{self.media.label}'"




class Survey(models.Model):
    name = models.CharField(max_length=250)
    # todo: determine how to select this and then make fields available for matching to category values
    # perhaps this is a url to a published service?
    # this way the data doesn't even need to be on same machine or network. could even be in agol
    map_service = models.URLField()
    # the querying the service based on extent or values would be much more straight forward
    # todo: limit the results of the data source to only select a subset.  This is for creating preload survey

    # store the fields from the service locally for reference in forms?
    service_config = models.TextField()
    # todo: these should be select lists from service_config
    media_field = models.CharField(max_length=200)
    facility_field = models.CharField(max_length=200)
    sub_facility_field = models.CharField(max_length=200)

    # sort_order = models.IntegerField(null=True, blank=True)




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
        assigned_questions = self.question_set.all()

        questions = [
            {
                'type': x.question.formatted_survey_field_type,
                'name': x.question.formatted_survey_field_name,
                'label': x.question.question,
                'relevant': x.question.formatted_survey_field_relevant,
                # 'media': x.question.media,
            } for x in assigned_questions
        ]
        questions_df = pd.DataFrame(questions)

        survey_df = orig_survey_df.append(questions_df)

        assigned_lookups = Lookup.objects.filter(group__masterquestion__surveyquestion__survey=self).distinct()
        choices = [
            {
                'list_name': x.group.formatted_survey_name,
                'name': x.formatted_survey_name,
                'label': x.description,
            } for x in assigned_lookups
        ]
        lookups_df = pd.DataFrame(choices)
        choices_df = orig_choices_df.append(lookups_df)

        with pd.ExcelWriter(output_survey, mode='w') as writer:
            survey_df.to_excel(writer, sheet_name='survey', index=False)
            choices_df.to_excel(writer, sheet_name='choices', index=False)
        # return questions_df, choices_df

    class Meta:
        verbose_name = "Assessment"

    # todo: figure out how to publish survey123. it might have to be manual
    # todo: populate survey123 service with existing base data


# class SurveyQuestion(models.Model):
#     survey = models.ForeignKey('Survey', on_delete=models.PROTECT, related_name='questions')
#     question = models.ForeignKey('MasterQuestion', on_delete=models.PROTECT, unique=True)
#     sort_order = models.IntegerField(null=True, blank=True)

    # def __str__(self):
    #     return self.question.question


class SurveyQuestionSet(models.Model):
    survey = models.ForeignKey('Survey', on_delete=models.PROTECT, related_name='questions')
    question_set = models.ForeignKey('QuestionSet', on_delete=models.PROTECT, unique=True)



class QuestionSet(models.Model):
    # survey = models.ForeignKey('Survey', on_delete=models.PROTECT, related_name='question_set')
    name = models.CharField(max_length=250)
    owner = models.CharField(max_length=250)
    # question = models.ForeignKey('MasterQuestion', on_delete=models.PROTECT, unique=True)



class QuestionList(models.Model):
    set = models.ForeignKey('QuestionSet', on_delete=models.PROTECT, unique=True)
    question = models.ForeignKey('MasterQuestion', on_delete=models.PROTECT, unique=True)

    def __str__(self):
        return self.question.question





