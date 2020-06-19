from django.contrib import admin
from .models import *


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


class LookupInline(admin.TabularInline):
    model = Lookup
    extra = 0


@admin.register(LookupGroup)
class LookupGroupAdmin(admin.ModelAdmin):
    inlines = [LookupInline]


@admin.register(MasterQuestion)
class MasterQuestionAdmin(admin.ModelAdmin):
    list_filter = ['category__media']


class SurveyQuestionInline(admin.TabularInline):
    model = QuestionSet.surveys.through
    # ordering = ['sort_order']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [SurveyQuestionInline]
    # ordering = ['sort_order']


 # todo: add a method that checks to see if the map service url has been provided
 # todo: upon save, go out to the url and get the service properties and put them in the service config field
 # create class method and pass in user from request

class QuestionSetInline(admin.TabularInline):
    model = QuestionSet.questions.through


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