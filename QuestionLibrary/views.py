from django.shortcuts import render
from django.views.generic import View
from django.http.response import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from social_django.utils import load_strategy
import requests
import urllib
from QuestionLibrary.models import *
from wsgiref.util import FileWrapper
import csv
from django.contrib import messages


@method_decorator(login_required, name='dispatch')
class EsriProxy(View):
    def get_url(self, request):
        return request.META['QUERY_STRING'].split('?')[0]

    def get_token(self, request):
        social = request.user.social_auth.get(provider='agol')
        return social.get_access_token(load_strategy())

    def handle_esri_response(self, response):
        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers['Content-Type']
        )

    def get(self, request, format=None):
        try:
            url = self.get_url(request)
            token = self.get_token(request)

            '''Right now just allow all authorized users to use proxy but we can furthur filter access
            down to those who have access to the data intake'''
            # request.user.has_perm('aum.view_dataintake') # check if user has permission to download_xls_sheet data intakes
            '''we will need to build out further the row level access to data intake probably using django-guardian'''
            # data_dump = DataIntake.objects.get(pk=match.group(5)) # get obj to check permissions in teh future

            # put token in params and parse query params to new request
            params = dict(token=token) if 'services.arcgis.com/cJ9YHowT8TU7DUyn' in url else dict()
            for key, value in request.GET.items():
                if '?' in key:
                    key = key.split('?')[1]
                if key != 'auth_token':
                    params[key] = value

            r = requests.get(url, params=params)
            if r.status_code != requests.codes.ok:
                return HttpResponse(status=r.status_code)

            return self.handle_esri_response(r)

        except PermissionError:
            return HttpResponse(status=403)

        except Exception:
            return HttpResponse(status=500)

    def post(self, request):
        try:
            url = self.get_url(request)
            token = self.get_token(request)

            # for posts the token goes in a header
            r = requests.post(url, data=urllib.parse.unquote(request.body.decode('utf-8')),
                              headers={"X-Esri-Authorization": f"Bearer {token}",
                                       "Content-Type": "application/x-www-form-urlencoded"})
            if r.status_code != requests.codes.ok:
                return HttpResponse(status=r.status_code)

            return self.handle_esri_response(r)

        except:
            return HttpResponse(status=500)


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
    for obj in queryset:
        obj.postAttributes(request.user)
        messages.success(request, 'Records Successfully Loaded to Survery123')


load_selected_records_action.short_description = 'Load Selected Records to Survey123'
