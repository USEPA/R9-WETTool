from django.contrib import admin
from .models import *
from social_django.utils import load_strategy
from django.contrib.auth.models import User
import requests




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

    def getMapService(self):
        v = User.objects.first()
        social = v.social_auth.get(provider='agol')
        token = social.get_access_token(load_strategy())

        if Survey.objects.get(map_service = None):
            map_service = Survey.objects.get('map_service')
            r = requests.get(url=map_service, params={'token': token, 'f': 'json'})



    def saveSurvery(self, request, obj, form, change):

        obj.user = request.user
        super().save_model(request, obj, form, change)


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