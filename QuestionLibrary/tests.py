from django.test import TestCase
from unittest.mock import patch
import json

from QuestionLibrary.tasks import set_survey_to_submitted


def mock_requests_success(*args, **kwargs):
    class MockResponse:
        def json(self):
            return {
                'result': 'success'
            }

        def raise_for_status(self):
            pass

    return MockResponse()


class TaskRunnerTestCase(TestCase):
    @patch('QuestionLibrary.tasks.requests.post', side_effect=mock_requests_success)
    def test_set_survey_to_submitted(self, request_post):
        payload = {"feature": {"attributes": {"objectId": 1, "survey_status": None},
                               "layerInfo": {"id": 0, "objectIdField": "objectId"}},
                   "surveyInfo": {"serviceUrl": "http://test.url/FeatureServer"},
                   "portalInfo": {"token": "a_token"}}
        set_survey_to_submitted(payload)
        request_post.assert_called_with("http://test.url/FeatureServer/0/applyEdits",
                                        params={'token': 'a_token', 'f': 'json'},
                                        data={'updates': json.dumps({'attributes': {
                                            'objectid': 1,
                                            'survey_status': 'submitted'}
                                        })},
                                        headers={'Content-type': 'application/x-www-form-urlencoded'})
