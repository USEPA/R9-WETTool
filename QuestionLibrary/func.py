import json

from django.core.exceptions import ObjectDoesNotExist
from .models import MasterQuestion
import requests


def load_responses(survey, response_features, token, eventType):

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
        f = {'attributes': {}}
        for response_feature in response_features:
            for k, v in response_feature['attributes'].items():
                if k.startswith(layer_prefix):
                    f['attributes'][k.replace(layer_prefix, "")] = v

            # if layer is the base layer holding geometry grab it and put it back into base service
            if layer['id'] == int(survey.layer):
                f['geometry'] = response_feature.get('geometry', None)

            data = {'adds' if eventType == 'addData' else
                    ('updates' if eventType == 'editData' else None): [json.dumps(f)]}


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
                    if original_attribute in master_questions:
                        assessment_responses.append({'attributes': {
                            'question': master_questions[original_attribute].question,
                            'response': v,
                            'units': response_feature['attributes'][f"{original_attribute}_choices"],
                            'facility_id': fac_id,
                            'system_id': response_feature['attributes']['layer_0_pws_fac_id'],
                            'EditDate': response_feature['attributes']['EditDate']
                            # 'display_name':
                        }})
                elif k.endswith('_choices'):
                    pass

                elif k in master_questions:
                    master_question = master_questions[k]
                    try:
                        v_decoded = master_question.lookup.lookups.get(label=v).description
                    except ObjectDoesNotExist:
                        v_decoded = None
                    assessment_responses.append({'attributes': {
                        'question': master_questions[k].question,
                        'response': v,
                        'facility_id': fac_id,
                        'system_id': response_feature['attributes']['layer_0_pws_fac_id'],
                        'display_name': v_decoded,
                        'EditDate': response_feature['attributes']['EditDate']
                    }})

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
            for k, v in response.items():
                features[0]['attributes'][k] = v
            updates.append(features[0])
        else:
            adds.append(response)

    data = {'adds': json.dumps(adds), 'updates': json.dumps(updates)}
    requests.post(f"{survey.base_map_service}/{table['id']}/applyEdits", params={'token': token, 'f': 'json'},
                  data=data, headers={'Content-type': 'application/x-www-form-urlencoded'})



