from django.contrib import admin, sites
from .models import *
from django.forms import ModelForm, ModelChoiceField, CharField, HiddenInput
from django import forms
from django.core.exceptions import ValidationError
import json
from django.contrib.admin.widgets import AutocompleteSelect

from .views import download_xls_action, load_selected_records_action
from fieldsets_with_inlines import FieldsetsInlineMixin


# class MediaForm(ModelForm):
#     class Meta:
#         model = Media
#         exclude =[]
#         def __init__(self, *args, **kwargs):
#             # initial = kwargs.get('initial', {})
#             # initial['label'] = 'Media'
#             # kwargs['initial'] = initial
#             # # super(MediaForm, self).__init__(*args, **kwargs)


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ['label', 'description']
    # form= MediaForm
    pass


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    list_display = ['facility_type', 'fac_code', 'category']
    list_filter = ['category', 'facility_type']
    pass


#
# @admin.register(FacilitySubType)
# class FacilitySubTypeAdmin(admin.ModelAdmin):
#     pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['label', 'media']
    list_filter = ['media']
    pass


@admin.register(ResponseType)
class ResponseTypeAdmin(admin.ModelAdmin):
    pass


#
# @admin.register(Unit)
# class UnitAdmin(admin.ModelAdmin):
#     pass


@admin.register(FeatureServiceResponse)
class FeatureServiceResponseAdmin(admin.ModelAdmin):
    pass


class LookupInline(admin.TabularInline):
    model = Lookup
    extra = 0


@admin.register(LookupGroup)
class LookupGroupAdmin(admin.ModelAdmin):
    inlines = [LookupInline]


class QuestionFieldVal(ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionFieldVal, self).__init__(*args, **kwargs)
        self.fields['default_unit'].queryset = Lookup.objects.filter(group=self.instance.lookup)
        self.fields['facility_type'].queryset = FacilityType.objects.none()

        if self.instance.category_id is not None:
            try:
                # category_id = int(self.data.get('category'))
                self.fields['facility_type'].queryset = FacilityType.objects.filter(category=self.instance.category_id)
            except (ValueError, TypeError):
                pass

        media = self.cleaned_data['media'] if hasattr(self, 'cleaned_data') else getattr(self.instance, 'media', None)
        if media is not None:
            categories_queryset = Category.objects.filter(media=media)
            self.fields['category'].queryset = categories_queryset

            if categories_queryset.count() > 0:
                self.fields['category'].required = True

        # response_type = self.cleaned_data['response_type'] if hasattr(self, 'cleaned_data') else getattr(self.instance, 'response_type', None)
        # # lookup = self.cleaned_data['lookup'] if hasattr(self, 'cleaned_data') else getattr(self.instance, 'lookup', None)
        # if response_type is not None:
        #     self.fields['lookup'].required = False
        #     if response_type.label == 'select_one':
        #         self.fields['lookup'].required = True

    def clean_lookup(self):
        response_type = self.cleaned_data['response_type'] if hasattr(self, 'cleaned_data') else getattr(self.instance,
                                                                                                         'response_type',
                                                                                                         None)

        if response_type.label == 'select_one':
            if self.cleaned_data['lookup'] is None:
                raise ValidationError('Lookup required if Response Type is select_one.')
        return self.cleaned_data.get('lookup', None)

    def clean_category(self):
        # categories = Category.objects.filter(media=self.cleaned_data['media'])
        # if len(categories) == 0:
        #     self.cleaned_data['category'] = None
        category = self.cleaned_data['category'] if hasattr(self, 'cleaned_data') else getattr(self.instance,
                                                                                               'category', None)

        if category != 'All':
            if self.cleaned_data['category'] is None:
                raise ValidationError('Category required if not selecting all media types.')
        return self.cleaned_data.get('category', None)
        # else:
        #     raise ValidationError('Category required if not selecting all media types.')
        # elif self.cleaned_data['category'] not in categories:
        #     raise ValidationError('Category required if not selecting all media types.')
        # if len(categories) > 0 and self.cleaned_data['category'] in categories:
        #     self.fields['category'].queryset = categories
        #     raise ValidationError('Category required if not selecting all media types.')
        # elif len(categories) == 0:
        #     self.cleaned_data['category'] = None

        # return self.cleaned_data.get('category', None)


class Meta:
    model = MasterQuestion
    exclude = []


class RelatedQuestionInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RelatedQuestionInlineForm, self).__init__(*args, **kwargs)

        if self.instance.question_id is not None:
            self.fields['relevant_field'].queryset = Lookup.objects.filter(group=self.instance.question.lookup)


    class Meta:
        widgets = {
            'question': AutocompleteSelect(
                MasterQuestion.related_questions.through._meta.get_field('question').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true', 'style': 'width: 800px;'}
            ),
        }


class MasterQuestionRelatedQuestionInline(admin.TabularInline):
    fields = ['related', 'relevant_field']
    model = MasterQuestion.related_questions.through
    fk_name = 'question'
    form = RelatedQuestionInlineForm


@admin.register(RelatedQuestionList)
class RelatedQuestionListAdmin(admin.ModelAdmin):
    pass


@admin.register(MasterQuestion)
class MasterQuestionAdmin(admin.ModelAdmin):
    form = QuestionFieldVal
    inlines = [MasterQuestionRelatedQuestionInline]
    list_filter = ['media', 'category', 'facility_type']
    search_fields = ['question']
    list_display = ['question', 'media', 'category', 'facility_type']
    ordering = ['question']
    # #
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "facility_type":
    #         kwargs["queryset"] = FacilityType.objects.filter(category=self.)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SurveyAdminForm(ModelForm):
    selected_features = CharField(widget=HiddenInput(), required=False)

    # define an init here
    layer = forms.ChoiceField(choices=[], label='Feature Layer', required=False)
    assessment_layer = forms.ChoiceField(choices=[], label='Response Layer', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.service_config is not None:
            config = json.loads(self.instance.service_config)

            if type(config) is dict:
                layer_choice = [(x['id'], x['name']) for x in config['layers']]
                self.fields['layer'].choices = layer_choice

                layer_choice = [(x['id'], x['name']) for x in config['tables']]
                self.fields['assessment_layer'].choices = layer_choice

    class Meta:
        model = Survey
        exclude = []


class SurveyQuestionInline(admin.TabularInline):
    model = QuestionSet.surveys.through
    # ordering = ['sort_order']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [SurveyQuestionInline]

    form = SurveyAdminForm
    list_display = ['name', 'base_service_ready', 'survey_service_ready']

    fields = ['name', 'base_map_service', 'layer', 'assessment_layer', 'survey123_service', 'selected_features']
    actions = [download_xls_action, load_selected_records_action]

    def save_model(self, request, obj, form, change):
        # obj.user = request.user
        obj.getMapService(request.user)
        # obj.getBaseAttributes(request.user)
        super().save_model(request, obj, form, change)


# todo add button to grab attributes from base data and post to survey123 service. this might not be the best place for this. need to think this through and ask karl


class QuestionSetInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionSetInlineForm, self).__init__(*args, **kwargs)
        # self.fields['default_unit'].queryset = Lookup.objects.filter(group=self.instance.lookup)
        # self.fields['facility_type'].queryset = FacilityType.objects.none()
        # if self.instance.category_id is not None:
        #     try:
        #         # category_id = int(self.data.get('category'))
        #         self.fields['question'].queryset = FacilityType.objects.filter(category=self.instance.category_id)
        #     except (ValueError, TypeError):
        #         pass

    class Meta:
        widgets = {
            'question': AutocompleteSelect(
                QuestionSet.questions.through._meta.get_field('question').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true', 'style': 'width: 800px;'}
            ),
        }


class QuestionSetInline(admin.TabularInline):
    model = QuestionSet.questions.through
    ordering = ['sort_order']
    autocomplete_fields = ['question']
    form = QuestionSetInlineForm


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner']
    fields = ['name', 'owner', 'media', 'category', 'facility_type']
    # forms = QuestionSetFilters
    inlines = [QuestionSetInline]

# class RelatedQuestionInlineForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super(RelatedQuestionInlineForm, self).__init__(*args, **kwargs)
#         # self.fields['default_unit'].queryset = Lookup.objects.filter(group=self.instance.lookup)
#         # self.fields['facility_type'].queryset = FacilityType.objects.none()
#         # if self.instance.category_id is not None:
#         #     try:
#         #         # category_id = int(self.data.get('category'))
#         #         self.fields['question'].queryset = FacilityType.objects.filter(category=self.instance.category_id)
#         #     except (ValueError, TypeError):
#         #         pass
#
#     class Meta:
#         widgets = {
#             'question': AutocompleteSelect(
#                 RelatedQuestionList.questions.through._meta.get_field('question').remote_field,
#                 admin.site,
#                 attrs={'data-dropdown-auto-width': 'true', 'style': 'width: 800px;'}
#             ),
#         }
