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
from django.core.exceptions import PermissionDenied
import json
from social_django.utils import load_strategy
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

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

@csrf_exempt
def webhook(request):
    body_unicode = request.body.decode('utf-8')
    payload = json.loads(body_unicode)
    # if not expected event time then escape
    if payload['eventType'] not in ['addData', 'editData']:
        return HttpResponse("Ok")
    origin_features =[]
    #grab the survery and user info to display in the admin?
    survey = Survey.objects.get(survey123_service=payload['surveyInfo']['serviceUrl'])

    # updated_features = [{'surveyInfo': payload['surveyInfo']}, {'userInfo': payload['userInfo']}]
    # response = requests.get(f"{payload['portalInfo']['url']}/sharing/rest/community/self",
    #                         params=dict(token=request.data['portalInfo']['token'], f='json'), timeout=30)
    # # if response.status_code != requests.codes.ok or 'error' in response.text or request.data['userInfo']['username'] != response.json().get('username', ''):
    # #     raise PermissionDenied

    #not sure if we will need origin_feature at any point
    # origin_feature = {'attributes': payload['feature'].get('attributes'), 'geometry': payload['feature'].get('geometry', None)}
    token = payload['portalInfo']['token']
    # loop through the edited data and grab the attributes & geometries while scrubbing the base_ prefix off of the fields
    for features in payload['applyEdits']:
        base_service_config = json.loads(survey.service_config)['layers']
        # todo: deal with new features and how that affects creating records in related tables
        for layer in base_service_config:
            layer_prefix = f"layer_{layer['id']}_"

            # translate fields for this service into their original name and post back
            f = {'attributes': {}}
            for k, v in payload['feature']['attributes'].items():
                if k.startswith(layer_prefix):
                    f['attributes'][k.replace(layer_prefix, "")] = v

            # if layer is the base layer holding geometry grab it and put it there
            if layer['id'] == survey.layer:
                f['geometry'] = payload['feature'].get('geometry', None)


            data = {'adds' if payload['eventType'] == 'addData' else
                    ('updates' if payload['eventType'] == 'editData' else None): [json.dumps(f)]}

            # todo: for updates look for existing record and copy to history table

            response = requests.post(f"{survey.base_map_service}/{layer['id']}/applyEdits", params={'token': token, 'f': 'json'},
                          data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})

            # if m['attributes']['survey_status'] == '':
            #     m['attributes']['survey_status'] = 'needs_review'
            # updated = {'attributes': {}, 'geometry': m['geometry']}
        table = next(x for x in json.loads(survey.service_config)['tables'] if x['id'] == int(survey.assessment_layer))
        master_questions = {q.formatted_survey_field_name: q.question for q in MasterQuestion.objects.all()}
        assessment_responses = []
        # todo: add foreign key back to parent feature
        for k, v in payload['feature']['attributes'].items():
            if not k.startswith('layer'):
                if k.endswith('_measure'):
                    original_attribute = k.replace('_measure', '')
                    if original_attribute in master_questions:
                        assessment_responses.append({'attributes': {
                            'question': master_questions[original_attribute],
                            'answer': v,
                            'units': payload['feature']['attributes'][f"{original_attribute}_choices"]
                        }})
                elif k.endswith('_choices'):
                    pass
                elif k in master_questions:
                    assessment_responses.append({'attributes': {
                        'question': master_questions[k],
                        'answer': v
                    }})

        data = {'adds': json.dumps(assessment_responses)}
        requests.post(f"{survey.base_map_service}/{table['id']}/applyEdits", params={'token': token, 'f': 'json'},
                      data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})

    return HttpResponse("Ok")




