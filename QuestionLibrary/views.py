from django.shortcuts import render
from django.views.generic import View
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from social_django.utils import load_strategy
import requests


@method_decorator(login_required, name='dispatch')
class EsriProxy(View):
    # authentication_classes = (SessionAuthentication, TokenAuthSupportQueryString)

    # def perform_content_negotiation(self, request, force=False):
    #     """
    #     override to always use default rendering
    #     """
    #     renderers = self.get_renderers()
    #     # conneg = self.get_content_negotiator()

        # return (renderers[0], renderers[0].media_type)

    def get_url(self, request):
        return request.META['QUERY_STRING'].split('?')[0]

    def get_token(self, request):
        social = request.user.social_auth.get(provider='agol')
        return social.get_access_token(load_strategy())

        # now = dt.utcnow().replace(tzinfo=pytz.UTC)
        # token_dict = cache.get('ARC_SERVER_TOKEN')
        #
        # if self.username and self.password and (token_dict is None or (not token_dict['token'] or token_dict['token_expiration'] < now)):
        #
        #     token_request = requests.post('https://epa.maps.arcgis.com/sharing/rest/generateToken',
        #                                   data={'username': self.username, 'password': self.password,
        #                                         'f': 'json', 'referer': self.request.headers['Origin']})
        #     if token_request.status_code == requests.codes.ok:
        #         expires = dt.utcfromtimestamp(token_request.json()['expires'] / 1000).replace(tzinfo=pytz.UTC)
        #         token_dict = dict(token=token_request.json()['token'], token_expiration=expires)
        #         cache.set('ARC_SERVER_TOKEN', token_dict)
        #
        # return token_dict['token']

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
            # request.user.has_perm('aum.view_dataintake') # check if user has permission to view data intakes
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
            r = requests.post(url, request.data, headers={"X-Esri-Authorization": f"Bearer {token}"})
            if r.status_code != requests.codes.ok:
                return HttpResponse(status=r.status_code)

            return self.handle_esri_response(r)

        except:
            return HttpResponse(status=500)
