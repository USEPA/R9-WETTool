import requests
from django.conf import settings
from django.contrib.auth.models import User
from pandas import DataFrame
from social_django.utils import load_strategy
from numpy import nan as not_a_number

class TokenExpired(Exception):
    pass


def formattedFieldName(layer_id, field_name):
    return f"layer_{layer_id}_{field_name}"


def get_all_features(url, token, where="1=1"):
    offset = 0
    limit = 100
    r = None
    f = []
    while True:
        data = {"token": token, "f": "json", "where": where, "outFields": "*",
                "resultRecordCount": limit, "resultOffset": offset, "exceedTransferLimit": True}
        response = requests.post(f"{url}/query", data=data)

        response_json = response.json()

        if r is None:
            r = response_json

        if "error" in response_json:
            if response_json["error"]["code"] == 498:
                raise TokenExpired(response.content)

            raise Exception(response.content)

        if len(response_json["features"]) > 0:
            f += response_json["features"]
            offset += limit
        else:
            break
        r['features'] = f
    return r


def get_token():
    user = User.objects.get(username=settings.TASK_RUNNER_AGOL_USER)
    social = user.social_auth.get(provider='agol')
    token = social.get_access_token(load_strategy())
    if token is None:
        raise Exception('AGOL Token expired')
    return token

def get_latest_assessment_responses(group_by_field, assessment_responses, current_responses):
    group_by_fields = ['question', group_by_field]
    adds, updates = [], []
    if len(assessment_responses) > 0:
        assessment_responses_df = DataFrame(assessment_responses)
        assessment_responses_df = assessment_responses_df.loc[
                                  assessment_responses_df.groupby(group_by_fields,
                                                                  dropna=False).EditDate.idxmax(), :]
        assessment_responses_df = assessment_responses_df.replace({not_a_number: None})
        assessment_responses = [{'attributes': x} for x in assessment_responses_df.to_dict('records')]
        # loop through assessment questions and check if they need to be added or updated in base service
        for response in assessment_responses:
            # only looking at system id or facility id so facility id has to be unique across datasets... switch to actual PK for this?
            # but likelihood of same question for same fac id at this point is very low
            features = list(filter(
                lambda f: f['attributes']['question'] == response['attributes']['question'] and f['attributes'][group_by_field] == response['attributes'][group_by_field],
                current_responses['features']
            ))
            if len(features) == 1:
                for k, v in response['attributes'].items():
                    features[0]['attributes'][k] = v
                updates.append(features[0])
            else:
                adds.append(response)

    return adds, updates
