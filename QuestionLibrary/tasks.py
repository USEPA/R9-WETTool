from urllib.parse import urlencode

import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from pandas import DataFrame

from QuestionLibrary.func import formattedFieldName
from QuestionLibrary.models import Survey, MasterQuestion
import json
import requests
from dramatiq import actor



@actor()
def set_survey_to_submitted(payload, token):
    # updated_features = [{'surveyInfo': payload['surveyInfo']}, {'userInfo': payload['userInfo']}]
    # response = requests.get(f"{payload['portalInfo']['url']}/sharing/rest/community/self",
    #                         params=dict(token=request.data['portalInfo']['token'], f='json'), timeout=30)
    # # if response.status_code != requests.codes.ok or 'error' in response.text or request.data['userInfo']['username'] != response.json().get('username', ''):
    # #     raise PermissionDenied

    # not sure if we will need origin_feature at any point
    # origin_feature = {'attributes': payload['feature'].get('attributes'), 'geometry': payload['feature'].get('geometry', None)}

    # flip the survey status field to submitted in the survey service in
    # the survey inbox will be filtered to only show survey status = null
    survey_status_switch = []
    for k, v in payload['feature']['attributes'].items():
        if k == 'survey_status':
            survey_status_switch.append({'attributes': {
                'objectid': payload['feature']['result']['objectId'],
                'survey_status': 'submitted'}})
    data_status = {'updates': json.dumps(survey_status_switch)}
    requests.post(f"{payload['surveyInfo']}/0/applyEdits", params={'token': token, 'f': 'json'},
                  data=data_status, headers={'Content-type': 'application/x-www-form-urlencoded'})


# load_responses(survey, [payload['feature']], token, payload['eventType'])
@transaction.atomic
@actor()
def load_responses(survey_pk, response_features, token, eventType):
    survey = Survey.objects.get(pk=survey_pk)
    # updated_features = [{'surveyInfo': payload['surveyInfo']}, {'userInfo': payload['userInfo']}]
    # response = requests.get(f"{payload['portalInfo']['url']}/sharing/rest/community/self",
    #                         params=dict(token=request.data['portalInfo']['token'], f='json'), timeout=30)
    # # if response.status_code != requests.codes.ok or 'error' in response.text or request.data['userInfo']['username'] != response.json().get('username', ''):
    # #     raise PermissionDenied

    #not sure if we will need origin_feature at any point
    # origin_feature = {'attributes': payload['feature'].get('attributes'), 'geometry': payload['feature'].get('geometry', None)}



    # loop through the edited data and grab the attributes & geometries while scrubbing the base_ prefix off of the fields
    base_service_config = json.loads(survey.service_config)['layers']
    # todo: deal with new features and how that affects creating records in related tables
    for layer in base_service_config:
        layer_prefix = f"layer_{layer['id']}_"  # get prefix for this layers attributes

        # translate fields for this service into their original name and post back
        features = []
        for response_feature in response_features:
            f = {'attributes': {}}
            for k, v in response_feature['attributes'].items():
                if k.startswith(layer_prefix):
                    f['attributes'][k.replace(layer_prefix, "")] = v

            # if layer is the base layer holding geometry grab it and put it back into base service
            if layer['id'] == int(survey.layer):
                f['geometry'] = response_feature.get('geometry', None)
            features.append(f)
        data = {'adds' if eventType == 'addData' else
                ('updates' if eventType == 'editData' else None): json.dumps(features)}


            # todo: for updates look for existing record and copy to history table
            # ignore eventType and always check?? based on what? if someone can enter then what happens...
            # we need to pass global id from base into surveys and return back... if base globalid not populated then its new...?

        requests.post(f"{survey.base_map_service}/{layer['id']}/applyEdits",
                      params={'token': token, 'f': 'json'},
                      data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})

    table = next(x for x in json.loads(survey.service_config)['tables'] if x['id'] == int(survey.assessment_layer))
    assessment_responses = []
    for response_feature in response_features:
        fac_id = None
        if fac_id is None and response_feature['attributes'].get('layer_1_FacilityID') is not None:
           fac_id = response_feature['attributes']['layer_1_FacilityID']
        else:
            fac_id = None
        master_questions = {q.formatted_survey_field_name: q for q in MasterQuestion.objects.all()}
        for k, v in response_feature['attributes'].items():
            if not k.startswith('layer'):
                if k.endswith('_measure'):
                    original_attribute = k.replace('_measure', '')
                    units = response_feature['attributes'][f"{original_attribute}_choices"]
                    if original_attribute in master_questions:
                        assessment_responses.append({
                            # add measure to prevent collision with original question (likely due to misconfiguration of question)
                            'question': f"{master_questions[original_attribute].question} measure",
                            'response': v,
                            'units': units,
                            'facility_id': fac_id,
                            'system_id': response_feature['attributes']['layer_0_pws_fac_id'],
                            'EditDate': response_feature['attributes']['EditDate'],
                            'display_name': f"{v} {units}"
                        })
                elif k.endswith('_choices'):
                    pass

                elif k in master_questions:
                    master_question = master_questions[k]
                    try:
                        v_decoded = master_question.lookup.lookups.get(label=v).description
                    except ObjectDoesNotExist:
                        v_decoded = None
                    assessment_responses.append({
                        'question': master_questions[k].question,
                        'response': v,
                        'facility_id': fac_id,
                        'system_id': response_feature['attributes']['layer_0_pws_fac_id'],
                        'display_name': v_decoded,
                        'EditDate': response_feature['attributes']['EditDate']
                    })

    assessment_responses_df = DataFrame(assessment_responses)
    assessment_responses_df = assessment_responses_df.loc[assessment_responses_df.groupby(['question', 'system_id', 'facility_id'], dropna=False).EditDate.idxmax(),:]
    assessment_responses_df = assessment_responses_df.replace({np.nan: None})
    assessment_responses = [{'attributes': x} for x in assessment_responses_df.to_dict('records')]
    # loop through assessment questions and check if they need to be added or updated in base service
    updates, adds = [], []
    for response in assessment_responses:
        where = f"question='{response['attributes']['question']}' AND system_id='{response['attributes']['system_id']}'"
        if response['attributes']['facility_id'] is not None:
            where += f" AND facility_id='{response['attributes']['facility_id']}'"
        r = requests.get(f"{survey.base_map_service}/{table['id']}/query",
                         params={'where': where, 'token': token, 'f': 'json', 'outFields': '*'})
        features = r.json()['features']
        if len(features) == 1:
            for k, v in response['attributes'].items():
                features[0]['attributes'][k] = v
            updates.append(features[0])
        else:
            adds.append(response)

    data = {'adds': json.dumps(adds), 'updates': json.dumps(updates)}
    r = requests.post(f"{survey.base_map_service}/{table['id']}/applyEdits", params={'token': token, 'f': 'json'},
                  data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
    print(r)
    
@actor()
def load_surveys(service_url, token, features):
    # def postAttributes(self, user):
    data = urlencode({"adds": json.dumps(features)})

    delete_r = requests.post(url=f'{service_url}/0/deleteFeatures', params={'token': token, 'f': 'json'},
                      data={"where": "survey_status is null"}, headers={'Content-type': 'application/x-www-form-urlencoded'})

    add_r = requests.post(url=f'{service_url}/0/applyEdits', params={'token': token, 'f': 'json'},
                      data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
    
@actor()
def get_features_to_load(survey_pk, token):
    survey = Survey.objects.get(pk=survey_pk)
    # def getBaseAttributes(self, user):
    features = []
    # r = requests.get(url=self.base_map_service, params={'token': token, 'f': 'json'})

    service_config_layers = json.loads(survey.service_config)['layers']
    # get layers that serve a origin in relationship
    # origin_layers = [x for x in service_config_layers if
    #                  x['id'] = survey.layer]
    # any(y['role'] == 'esriRelRoleOrigin' for y in x['relationships'])] #service config for the selected layer x=origin_id?

    for x in service_config_layers:
        if x['id'] == int(survey.layer):
            origin_layer = x

            result_offset = 0
            related_responses = {}
            selected = survey.selected_features.split(',')

            object_ids = selected

            if len(object_ids) == 0:
                break
            else:
                result_offset += 10
                # get features in origin layer

            data = {"where": "1=1",
                    "objectIds": ','.join(object_ids),
                    # "resultOffset": result_offset,
                    # "resultRecordCount": 10,
                    "outFields": "*",
                    }

            params = {'token': token,
                      'f': 'json'}
            q = requests.post(url=survey.base_map_service + '/' + str(survey.layer) + '/query',
                              params=params, data=data)
            layer_name = origin_layer['name']

            # object_ids = [str(z['attributes']['OBJECTID']) for z in q.json()['features']]

            # get the related layer
            # todo: figure out where to pull geometry from... like froms base_facility_inventory... not the origin table
            for related_layer in [y for y in origin_layer['relationships']]:  # esriRelRoleDestination
                data = {"objectIds": ','.join(object_ids),
                        "relationshipId": related_layer['id'],
                        "outFields": "*",
                        }
                params = {'token': token,
                          'f': 'json'}
                related_responses[related_layer['id']] = requests.post(
                    url=survey.base_map_service + '/' + str(survey.layer) + '/queryRelatedRecords',
                    params=params, data=data)

                # deconstruct the queryRelatedRecords response for easier handling since we only have 1 objectid at a time
            for origin_feature in q.json()['features']:
                # loop through relationships to get all features in all related layers
                feature = {'attributes': {}, 'geometry': origin_feature.get('geometry', None)}

                for k, v in origin_feature['attributes'].items():
                    feature['attributes'][formattedFieldName(x['id'], k)] = v

                for related_layer_id, related_response in related_responses.items():
                    related_features = [z['relatedRecords'][0] for z in
                                        related_response.json()['relatedRecordGroups']
                                        if z['objectId'] == origin_feature['attributes']['OBJECTID']]
                    for related_feature in related_features:

                        # this is fair dynamic but geometry needs to be captured correctly
                        # this should work correctly based on our current understanding of how the data is structured and fall back to
                        # the origin geometry if related records isn't the for some reason
                        if feature.get('geometry', None) is None:
                            feature['geometry'] = related_feature.get('geometry', None)

                        for k, v in related_feature['attributes'].items():
                            feature['attributes'][formattedFieldName(related_layer_id, k)] = v

                # set default values for survey123 questions for existing features from base data
                for question_set in survey.question_set.all():
                    for question in question_set.questions.all():
                        if question.relevant_for_feature(feature, survey.layer) and question.default_unit is not None:
                            feature['attributes'][
                                f'{question.formatted_survey_field_name}_choices'] = question.default_unit.description

                features.append(feature)
                # print(feature)

            # print(features)
    return features