from django.shortcuts import render
from django.views.generic import View
from django.http.response import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from dramatiq import pipeline
from social_django.utils import load_strategy
import requests
import urllib

from QuestionLibrary.tasks import load_responses, set_survey_to_submitted, process_response_features
from QuestionLibrary.models import *
from wsgiref.util import FileWrapper
import csv
from django.core.exceptions import PermissionDenied
import json
from social_django.utils import load_strategy
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
import logging
logger = logging.getLogger('django')

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


@csrf_exempt
def webhook(request):
    body_unicode = request.body.decode('utf-8')
    try:
        payload = json.loads(body_unicode)
        # if not expected event time then escape
        if payload['eventType'] not in ['addData', 'editData']:
            return HttpResponse("Ok")

        survey = Survey.objects.get(survey123_service=payload['surveyInfo']['serviceUrl'])


        pipeline([
            set_survey_to_submitted.message(payload),
            process_response_features.message_with_options(survey.base_map_service, survey.service_config, survey.layer,
                                              payload['portalInfo']['token'], payload['eventType'],
                                              [payload['feature']], pipe_ignore=True),
            load_responses.message(survey.base_map_service, survey.service_config, survey.assessment_layer,
                                   payload['portalInfo']['token'])
        ]).run()

        # loop through the edited data and grab the attributes & geometries while scrubbing the base_ prefix off of the fields
        # base_service_config = json.loads(survey.service_config)['layers']
        # # todo: deal with new features and how that affects creating records in related tables
        # for layer in base_service_config:
        #     layer_prefix = f"layer_{layer['id']}_"
        #
        #     # translate fields for this service into their original name and post back
        #     f = {'attributes': {}}
        #     for k, v in payload['feature']['attributes'].items():
        #         if k.startswith(layer_prefix):
        #             f['attributes'][k.replace(layer_prefix, "")] = v
        #
        #     # if layer is the base layer holding geometry grab it and put it there
        #     if layer['id'] == int(survey.layer):
        #         f['geometry'] = payload['feature'].get('geometry', None)
        #
        #     data = {'adds' if payload['eventType'] == 'addData' else
        #             ('updates' if payload['eventType'] == 'editData' else None): [json.dumps(f)]}
        #
        #     # todo: for updates look for existing record and copy to history table
        #
        #     response = requests.post(f"{survey.base_map_service}/{layer['id']}/applyEdits",
        #                              params={'token': token, 'f': 'json'},
        #                              data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
        #
        # table = next(x for x in json.loads(survey.service_config)['tables'] if x['id'] == int(survey.assessment_layer))
        # fac_id = None
        # if fac_id is None and payload['feature']['attributes'].get('layer_1_FacilityID') is not None:
        #    fac_id = payload['feature']['attributes']['layer_1_FacilityID']
        # else:
        #     fac_id = None
        # master_questions = {q.formatted_survey_field_name: q for q in MasterQuestion.objects.all()}
        # assessment_responses = []
        # for k, v in payload['feature']['attributes'].items():
        #     if not k.startswith('layer'):
        #         if k.endswith('_measure'):
        #             original_attribute = k.replace('_measure', '')
        #             if original_attribute in master_questions:
        #                 assessment_responses.append({'attributes': {
        #                     'question': master_questions[original_attribute].question,
        #                     'response': v,
        #                     'units': payload['feature']['attributes'][f"{original_attribute}_choices"],
        #                     'facility_id': fac_id,
        #                     'system_id': payload['feature']['attributes']['layer_0_pws_fac_id'],
        #                     # 'display_name':
        #                 }})
        #         elif k.endswith('_choices'):
        #             pass
        #
        #         elif k in master_questions:
        #             master_question = master_questions[k]
        #             try:
        #                 v_decoded = master_question.lookup.lookups.get(label=v).description
        #             except ObjectDoesNotExist:
        #                 v_decoded = None
        #             assessment_responses.append({'attributes': {
        #                 'question': master_questions[k].question,
        #                 'response': v,
        #                 'facility_id':fac_id,
        #                 'system_id': payload['feature']['attributes']['layer_0_pws_fac_id'],
        #                 'display_name': v_decoded
        #
        #
        #             }})
        #
        # data = {'adds': json.dumps(assessment_responses)}
        # requests.post(f"{survey.base_map_service}/{table['id']}/applyEdits", params={'token': token, 'f': 'json'},
        #               data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})

        return HttpResponse("Ok")
    except Exception as e:
        logger.exception(body_unicode)
        raise e




