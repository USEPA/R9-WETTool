from django.contrib import admin
from .models import *
from django.forms import ModelForm, ModelChoiceField, CharField, HiddenInput
from django import forms
from django.core.exceptions import ValidationError
import requests, json
from django.http.response import HttpResponse

from .views import download_xls_action, load_selected_records_action


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    pass


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    pass


#
# @admin.register(FacilitySubType)
# class FacilitySubTypeAdmin(admin.ModelAdmin):
#     pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
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

        if self.instance.media_id is not None:
            self.fields['category'].queryset = Category.objects.filter(media=self.instance.media_id)

    def clean_lookup(self):
        if LookupGroup.objects.filter(
                label=self.cleaned_data.get('response_type', None)).exists() and not self.cleaned_data.get('lookup',
                                                                                                           None):
            raise ValidationError('Select proper Lookup')
        return self.cleaned_data.get('lookup', None)


    class Meta:
        model = MasterQuestion
        exclude = []


@admin.register(MasterQuestion)
class MasterQuestionAdmin(admin.ModelAdmin):
    form = QuestionFieldVal
    list_filter = ['category__media']
    # #
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "facility_type":
    #         kwargs["queryset"] = FacilityType.objects.filter(category=self.)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)



class SurveyAdminForm(ModelForm):
    selected_features = CharField(widget=HiddenInput(), required=False)

    # define an init here
    layer = forms.ChoiceField(choices=[], label='Feature Layer', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.service_config is not None:
            config = json.loads(self.instance.service_config)

            layer_choice = [(x['id'], x['name']) for x in config]
            self.fields['layer'].choices = layer_choice

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

    fields = ['name', 'base_map_service', 'layer', 'survey123_service', 'service_config', 'selected_features']
    actions = [download_xls_action, load_selected_records_action]

    def save_model(self, request, obj, form, change):
        # obj.user = request.user
        obj.getMapService(request.user)
        # obj.getBaseAttributes(request.user)
        super().save_model(request, obj, form, change)


# todo add button to grab attributes from base data and post to survey123 service. this might not be the best place for this. need to think this through and ask karl


class QuestionSetInline(admin.TabularInline):
    model = QuestionSet.questions.through
    ordering = ['sort_order']


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner']
    fields = ['name', 'owner']
    inlines = [QuestionSetInline]

# class JobsInlines(admin.TabularInline):
#     model = Survey
#
# @admin.register(Job)
# class JobsAdmin(admin.ModelAdmin):
#     inlines = [JobsInlines]
