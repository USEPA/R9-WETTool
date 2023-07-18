from django.contrib import admin, sites
from django.http import HttpResponse
from django.utils.timezone import now
from dramatiq import pipeline

from .models import *
from django.forms import ModelForm, ModelChoiceField, CharField, HiddenInput
from django import forms
from django.core.exceptions import ValidationError
import json
from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib import messages
from fieldsets_with_inlines import FieldsetsInlineMixin
from .tasks import load_responses, get_features_to_load, load_surveys, get_submitted_responses, \
    process_response_features, approve_draft_dashboard_service
from datetime import datetime


def load_selected_responses(modeladmin, request, queryset):
    for survey in queryset:
        social = request.user.social_auth.get(provider='agol')
        token = social.get_access_token(load_strategy())

        pipeline([
            get_submitted_responses.message(survey.survey123_service, token),
            process_response_features.message(survey.map_service_url, survey.epa_response.map_service_config, survey.layer, token, 'editData'),
            load_responses.message(survey.map_service_url, survey.epa_response.map_service_config, survey.assessment_layer, token, 'editData', None)
        ]).run()

        messages.success(request, 'Loading latest responses')


load_selected_responses.short_description = 'Get latest submitted responses from survey'


def download_xls_action(modeladmin, request, queryset):
    for obj in queryset:
        Survey.generate_xlsform(obj)
        path = os.path.join(settings.BASE_DIR, f'QuestionLibrary\\generated_forms\\{obj.id}.xlsx')
        excel = open(path, "rb")
        response = HttpResponse(excel, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=survey_config_service_{obj.name}.xlsx'
        # messages.success(request, 'Download Successful')
        return response


download_xls_action.short_description = 'Download Survey123 Service Configuration'


def load_selected_records_action(modeladmin, request, queryset):
    social = request.user.social_auth.get(provider='agol')
    token = social.get_access_token(load_strategy())

    for obj in queryset:
        pipeline([
            get_features_to_load.message(obj.pk, token),
            load_surveys.message(obj.survey123_service, token)
        ]).run()
        messages.success(request, 'Loading selected records into survey')


load_selected_records_action.short_description = 'Load Selected Records to Survey123'


def disable_epa_response_action(modeladmin, request, queryset):
    queryset.update(disabled_date=now())


disable_epa_response_action.short_description = 'Disable selected EPA Responses'


def enable_epa_response_action(modeladmin, request, queryset):
    queryset.update(disabled_date=None)


enable_epa_response_action.short_description = 'Enable selected EPA Responses'


class SurveyInline(admin.TabularInline):
    model = Survey
    fields = ['name', 'survey123_service']
    show_change_link = True
    extra = 0

    # def has_change_permission(self, request, obj=None):
    #     return False

    def get_readonly_fields(self, request, obj=None):
        return list(super().get_fields(request, obj))

    def has_add_permission(self, request, obj=None):
        return False


class EPAResponseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EPAResponseForm, self).__init__(*args, **kwargs)
        # turn the layer id fields into dropdowns populated with the layers in base service config JSON
        # field labels as defined in the model would be overwritten, so we copy those to the new dropdown fields
        if self.instance.map_service_config is not None:
            self.fields['system_layer_id'] = forms.ChoiceField(choices=self.instance.get_layers_as_choices(),
                                                               label=self.fields['system_layer_id'].label)
            self.fields['facility_layer_id'] = forms.ChoiceField(choices=self.instance.get_layers_as_choices(),
                                                                 label=self.fields['facility_layer_id'].label)
        # else:
        #     self.fields['system_layer_id'].widget = forms.HiddenInput()
        #     self.fields['facility_layer_id'].widget = forms.HiddenInput()

    #  todo add button to grab attributes from base data and post to survey123 service. this might not be the best place for this. need to think this through and ask karl


@admin.register(EPAResponse)
class EPAResponseAdmin(admin.ModelAdmin):
    inlines = [SurveyInline]
    actions = [disable_epa_response_action, enable_epa_response_action]
    readonly_fields = ['_status', '_map_service_config']
    exclude = ['disabled_date', 'map_service_config']
    list_display = ['name', '_status', '_map_service_config']
    list_filter = ['disabled_date']
    search_fields = ['name']
    form = EPAResponseForm

    def _status(self, obj=None):
        if obj.disabled_date is None:
            return 'Active'
        else:
            return f'Disabled {obj.disabled_date.strftime("%Y-%m-%d")}'

    def _map_service_config(self, obj=None):
        if obj.map_service_config is None:
            return '-'
        else:
            config = json.loads(obj.map_service_config)
            if 'error' in config:
                return 'Error getting configuration'
            if 'layers' in config:
                return 'Configuration Downloaded'

    def save_model(self, request, obj, form, change):
        if 'map_service_url' in form.changed_data:
            obj.get_map_service(request.user)
        super().save_model(request, obj, form, change)

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(
            request, queryset, search_term,
        )
        # filter results in the autocomplete inline fields to only include active epa_responses
        if 'autocomplete' in request.path:
            queryset = self.model.objects.filter(disabled_date=None)

            if search_term:
                queryset = self.model.objects.filter(disabled_date=None, name__contains=search_term)

        return queryset, may_have_duplicates


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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['label', 'media']
    list_filter = ['media']
    pass


@admin.register(Survey123FieldType)
class Survey123FieldTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(ESRIFieldTypes)
class ESRIFieldTypesAdmin(admin.ModelAdmin):
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

            # if categories_queryset.count() > 0:
            #     self.fields['category'].required = True

        # survey123_field_type = self.cleaned_data['survey123_field_type'] if hasattr(self, 'cleaned_data') else getattr(self.instance, 'survey123_field_type', None)
        # # lookup = self.cleaned_data['lookup'] if hasattr(self, 'cleaned_data') else getattr(self.instance, 'lookup', None)
        # if survey123_field_type is not None:
        #     self.fields['lookup'].required = False
        #     if survey123_field_type.label == 'select_one':
        #         self.fields['lookup'].required = True

    def clean_lookup(self):
        survey123_field_type = self.cleaned_data['survey123_field_type'] if hasattr(self, 'cleaned_data') else getattr(self.instance,
                                                                                                                       'survey123_field_type',
                                                                                                                       None)

        if survey123_field_type.label == 'select_one':
            if self.cleaned_data['lookup'] is None:
                raise ValidationError('Lookup required if Field Type is select_one.')
        return self.cleaned_data.get('lookup', None)

    def clean_category(self):
        # categories = Category.objects.filter(media=self.cleaned_data['media'])
        # if len(categories) == 0:
        #     self.cleaned_data['category'] = None
        category = self.cleaned_data['category'] if hasattr(self, 'cleaned_data') else getattr(self.instance,
                                                                                               'category', None)
        #
        # if category != 'All':
        #     if self.cleaned_data['category'] is None:
        #         raise ValidationError('Category required if not selecting all media types.')
        # return self.cleaned_data.get('category', None)
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
        # filter the related question somehow to improve performance?
        # this obviously doesn't work since we are trying to set related questions.
        # self.fields['related'].queryset = RelatedQuestionList.objects.all().prefetch_related('related')

        if self.instance.question_id is not None:
            self.fields['relevant_field'].queryset = Lookup.objects.filter(group=self.instance.question.lookup)

    class Meta:
        widgets = {
            'related': AutocompleteSelect(
                MasterQuestion.related_questions.through._meta.get_field('related').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true', 'style': 'width: 800px;'}
            ),
        }


class MasterQuestionRelatedQuestionInline(admin.TabularInline):
    fields = ['related', 'relevant_field']
    model = MasterQuestion.related_questions.through
    fk_name = 'question'
    autocomplete_fields = ['related']
    form = RelatedQuestionInlineForm


@admin.register(RelatedQuestionList)
class RelatedQuestionListAdmin(admin.ModelAdmin):
    pass


@admin.register(MasterQuestion)
class MasterQuestionAdmin(admin.ModelAdmin):
    # Question List
    form = QuestionFieldVal
    inlines = [MasterQuestionRelatedQuestionInline]
    list_filter = ['media', 'category', 'facility_type']
    search_fields = ['question']
    list_display = ['question', 'media', 'category', 'facility_type']
    ordering = ['question']
    fields = ['question', 'media', 'category', 'facility_type', 'survey123_field_type', 'lookup', 'default_unit']


class SurveyAdminForm(ModelForm):
    selected_features = CharField(widget=HiddenInput(), required=False)

    # layer = forms.ChoiceField(choices=[], label='Feature Layer', required=False)
    # assessment_layer = forms.ChoiceField(choices=[], label='Survey Response Layer', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.epa_response and self.instance.epa_response.map_service_config is not None:
            self.fields['layer'] = forms.ChoiceField(choices=self.instance.epa_response.get_layers_as_choices(),
                                                     label=self.fields['layer'].label)
            self.fields['assessment_layer'] = forms.ChoiceField(choices=self.instance.epa_response.get_tables_as_choices(),
                                                                label=self.fields['assessment_layer'].label)

            # config = json.loads(self.instance.epa_response.map_service_config)
            # if type(config) is dict:
            #     layer_choice = [(x['id'], x['name']) for x in config['layers']]
            #     self.fields['layer'].choices = layer_choice
            #
            #     layer_choice = [(x['id'], x['name']) for x in config['tables']]
            #     self.fields['assessment_layer'].choices = layer_choice

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
    list_display = ['name', 'epa_response', 'base_service_ready', 'survey_service_ready']

    fields = ['name', 'epa_response', 'layer', 'assessment_layer', 'survey123_service', 'selected_features', '_base_map_service_url']
    search_fields = ['name']
    autocomplete_fields = ['epa_response']
    actions = [download_xls_action, load_selected_records_action, load_selected_responses]
    readonly_fields = ['_base_map_service_url']

    def _base_map_service_url(self, obj):
        # the javascript map needs this to use the base map service
        if obj.epa_response is None or obj.epa_response.map_service_config is None:
            return 'Error: Select an EPA response with valid map service config'
            # raise ValidationError(_('Error: Select an EPA response with valid map service config', code="Invalid"))
        else:
            return format_html(
                '<span id="id_base_service_url">{}</span>',
                mark_safe(obj.epa_response.map_service_url)
            )

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
    fields = ['name', 'owner']
    # forms = QuestionSetFilters
    inlines = [QuestionSetInline]


def approve_dashboard(modeladmin, request, queryset):
    social = request.user.social_auth.get(provider='agol')
    token = social.get_access_token(load_strategy())

    for dashboard in queryset:
        pipeline([
            approve_draft_dashboard_service.message(dashboard.base_feature_service,
                                                    dashboard.draft_service_view,
                                                    dashboard.production_service_view,
                                                    token)
        ]).run()

        messages.success(request, 'Approving dashboard')


approve_dashboard.short_description = 'Approve selected dashboard(s)'


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'view_draft', 'view_production']
    actions = [approve_dashboard]
