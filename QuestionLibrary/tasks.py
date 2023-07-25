from urllib.parse import urlencode

import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from pandas import DataFrame

from QuestionLibrary.func import formattedFieldName, get_all_features, TokenExpired, get_token, \
    get_latest_assessment_responses, get_edit_date
from QuestionLibrary.models import Survey, MasterQuestion
import json
import requests
from dramatiq import actor
import logging

logger = logging.getLogger('dramatiq')


@actor()
def set_survey_to_submitted(payload):
    # updated_features = [{'surveyInfo': payload['surveyInfo']}, {'userInfo': payload['userInfo']}]
    # response = requests.get(f"{payload['portalInfo']['url']}/sharing/rest/community/self",
    #                         params=dict(token=request.data['portalInfo']['token'], f='json'), timeout=30)
    # # if response.status_code != requests.codes.ok or 'error' in response.text or request.data['userInfo']['username'] != response.json().get('username', ''):
    # #     raise PermissionDenied

    # not sure if we will need origin_feature at any point
    # origin_feature = {'attributes': payload['feature'].get('attributes'), 'geometry': payload['feature'].get('geometry', None)}

    # flip the survey status field to submitted in the survey service in
    # the survey inbox will be filtered to only show survey status = null

    if 'survey_status' in payload['feature']['attributes']:

        token = payload['portalInfo']['token']
        data = {'updates': json.dumps({'attributes': {
            'objectid': payload['feature']['result']['objectId'],
            'survey_status': 'submitted'}})
        }
        r = requests.post(f"{payload['surveyInfo']['serviceUrl']}/{payload['feature']['layerInfo']['id']}/applyEdits",
                          params={'token': token, 'f': 'json'},
                          data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
        r.raise_for_status()  # if 400 or 500s truly occur then raise error so retry occurs


@actor()
def get_submitted_responses(survey_service, token):
    token = get_token()
    response = requests.get(f"{survey_service}/0/query",
                            params={"where": "survey_status = 'submitted'", "outFields": "*", "token": token,
                                    "f": "json"})
    response.raise_for_status()
    r_json = response.json()
    if 'error' in r_json:
        # log but don't retry
        logger.error(['get_submitted_responses', response.content])

    return r_json.get('features', [])


@actor()
def process_response_features(survey_base_map_service, survey_service_config, survey_layer, token, eventType,
                              response_features):
    try:
        token = get_token() # override for now
        # loop through the edited data and grab the attributes & geometries while scrubbing the base_ prefix
        # off of the fields
        base_service_config = json.loads(survey_service_config)['layers']
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
                if layer['id'] == int(survey_layer):
                    f['geometry'] = response_feature.get('geometry', None)
                features.append(f)

            # if the layer being updated is the selected survey layer then allow adds
            # otherwise only allow updates b/c there should be no way of adding things
            if layer['id'] == int(survey_layer):
                data = {'adds' if eventType == 'addData' else
                        ('updates' if eventType == 'editData' else None): json.dumps(features)}
            else:
                data = {'updates': json.dumps(features)}
            # todo: for updates look for existing record and copy to history table
            # ignore eventType and always check?? based on what? if someone can enter then what happens...
            # we need to pass global id from base into surveys and return back... if base globalid not populated then its new...?

            r = requests.post(f"{survey_base_map_service}/{layer['id']}/applyEdits",
                              params={'token': token, 'f': 'json'},
                              data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
            if 'error' in r.json():
                # log but don't retry
                logger.error(['process_response_features', r.content, data])

        return response_features  # pass through pipeline so load_responses can run on these responses
    except Exception as e:
        logger.error(['process_response_features', response_features])
        raise e


@actor()
def load_responses(survey_base_map_service, survey_service_config, survey_assessment_layer, token, eventType, received_timestamp, response_features):
    try:
        token = get_token() # override for now
        # updated_features = [{'surveyInfo': payload['surveyInfo']}, {'userInfo': payload['userInfo']}]
        # response = requests.get(f"{payload['portalInfo']['url']}/sharing/rest/community/self",
        #                         params=dict(token=request.data['portalInfo']['token'], f='json'), timeout=30)
        # # if response.status_code != requests.codes.ok or 'error' in response.text or request.data['userInfo']['username'] != response.json().get('username', ''):
        # #     raise PermissionDenied

        # not sure if we will need origin_feature at any point
        # origin_feature = {'attributes': payload['feature'].get('attributes'), 'geometry': payload['feature'].get('geometry', None)}

        table = next(x for x in json.loads(survey_service_config)['tables'] if x['id'] == int(survey_assessment_layer))
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
                                'system_id': response_feature['attributes'].get('layer_0_pws_fac_id', None),
                                'EditDate': get_edit_date(response_feature, eventType, received_timestamp),
                                'display_name': f"{v} {units}"
                            })
                    elif k.endswith('_choices'):
                        pass

                    elif k in master_questions:
                        master_question = master_questions[k]
                        try:
                            if master_question.lookup is not None:
                                v_decoded = master_question.lookup.lookups.get(label=v).label
                            else:
                                v_decoded = v
                        except ObjectDoesNotExist:
                            v_decoded = v
                        assessment_responses.append({
                            'question': master_questions[k].question,
                            'response': v,
                            'facility_id': fac_id,
                            'system_id': response_feature['attributes'].get('layer_0_pws_fac_id', None),
                            'display_name': v_decoded,
                            'EditDate': get_edit_date(response_feature, eventType, received_timestamp)
                        })
        pre_grouped_assessments = {
            'facility_id': [x for x in assessment_responses if x['facility_id'] is not None],
            'system_id': [x for x in assessment_responses if x['facility_id'] is None]
        }
        captured_responses = {
            'facility_id': get_all_features(f"{survey_base_map_service}/{table['id']}", token, "facility_id is not null"),
            'system_id': get_all_features(f"{survey_base_map_service}/{table['id']}", token, "facility_id is null")
        }
        updates, adds = [], []
        for field, assessment_responses in pre_grouped_assessments.items():
            a, u = get_latest_assessment_responses(field, assessment_responses, captured_responses[field])
            adds += a
            updates += u

        data = {'adds': json.dumps(adds), 'updates': json.dumps(updates)}
        r = requests.post(f"{survey_base_map_service}/{table['id']}/applyEdits",
                          params={'token': token, 'f': 'json'},
                          data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
        if 'error' in r.json():
            logger.error(['load_responses error', r.json(), response_features])
    except Exception as e:
        logger.error(['load_responses exception', response_features])
        raise e


@actor()
def load_surveys(service_url, token, features):
    token = get_token()  # override for now
    data = urlencode({"adds": json.dumps(features)})

    delete_r = requests.post(url=f'{service_url}/0/deleteFeatures', params={'token': token, 'f': 'json'},
                             data={"where": "survey_status is null"},
                             headers={'Content-type': 'application/x-www-form-urlencoded'})
    if 'error' in delete_r.json():
        logger.error(['load_surveys', delete_r.content])

    add_r = requests.post(url=f'{service_url}/0/applyEdits', params={'token': token, 'f': 'json'},
                          data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})
    if 'error' in add_r.json():
        logger.error(['load_surveys', add_r.content])


@actor()
def get_features_to_load(survey_pk, token):
    token = get_token()  # override for now
    survey = Survey.objects.get(pk=survey_pk)
    features = []
    service_config_layers = json.loads(survey.epa_response.map_service_config)['layers']
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
            q = requests.post(url=survey.epa_response.map_service_url + '/' + str(survey.layer) + '/query',
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
                    url=survey.epa_response.map_service_url + '/' + str(survey.layer) + '/queryRelatedRecords',
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
                        if question.relevant_for_feature(feature, survey) and question.default_unit is not None:
                            feature['attributes'][
                                f'{question.formatted_survey_field_name}_choices'] = question.default_unit.description

                features.append(feature)
                # print(feature)

            # print(features)
    return features


@actor
def approve_draft_dashboard_service(base_service_url, draft_service_url, approved_service_url):
    token = get_token()
    # prep removing current features
    current_features_json = get_all_features(approved_service_url, token)

    delete_features = []
    for f in current_features_json["features"]:
        # if here is just a safety net in case someone swaps services accidentially
        if f['attributes']['qc_status'] == 'approved':
            delete_features.append(f['attributes'][current_features_json['objectIdFieldName']])

    # prep adding draft features to approved
    draft_features_json = get_all_features(draft_service_url, token)

    add_features = []
    for f in draft_features_json["features"]:
        # if here is just a safety net in case someone swaps services accidentially
        if f['attributes']['qc_status'] == 'draft':
            keys = [k for k in f['attributes']]
            [f['attributes'].pop(k) for k in keys if k.lower() in ['objectid', 'globalid']]
            f['attributes']['qc_status'] = 'approved'
            add_features.append(f)

    # add new approved features and delete old ones from base service
    data = urlencode({"adds": json.dumps(add_features), "deletes": json.dumps(delete_features)})
    update_features_response = requests.post(f"{base_service_url}/applyEdits", params={"token": token, "f": "json"},
                                             data=data,
                                             headers={'Content-type': 'application/x-www-form-urlencoded'})
    if "error" in update_features_response.json():
        logger.error(['approve_draft_dashboard_service', update_features_response.content])
