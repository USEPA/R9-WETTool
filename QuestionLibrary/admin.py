from django.contrib import admin
from .models import *
from django.forms import ModelForm, ModelChoiceField, CharField
from django.core.exceptions import ValidationError


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    pass


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(FacilitySubType)
class FacilitySubTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(ResponseType)
class ResponseTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    pass


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


    def clean_lookup(self):
        if LookupGroup.objects.filter(label=self.cleaned_data.get('response_type', None)).exists() and not self.cleaned_data.get('lookup', None):
            raise ValidationError('Select proper Lookup')
        return self.cleaned_data.get('lookup', None)

    class Meta:
        model = MasterQuestion
        exclude = []


@admin.register(MasterQuestion)
class MasterQuestionAdmin(admin.ModelAdmin):
    form = QuestionFieldVal
    list_filter = ['category__media']
    #
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "default_unit":
    #         kwargs["queryset"] = Lookup.objects.all()
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SurveyQuestionInline(admin.TabularInline):
    model = QuestionSet.surveys.through
    # ordering = ['sort_order']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [SurveyQuestionInline]


    def save_model(self, request, obj, form, change):
        # obj.user = request.user
        obj.getMapService(request.user)
        obj.getBaseAttributes(request.user)
        super().save_model(request, obj, form, change)


#todo add button to grab attributes from base data and post to survey123 service. this might not be the best place for this. need to think this through and ask karl


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
