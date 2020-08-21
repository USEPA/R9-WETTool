from django.shortcuts import render
from django.views.generic import View
from django.http.response import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from social_django.utils import load_strategy
import requests
import urllib
from QuestionLibrary.models import *
from wsgiref.util import FileWrapper



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
            r = requests.post(url, data=urllib.parse.unquote(request.body.decode('utf-8')), headers={"X-Esri-Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"})
            if r.status_code != requests.codes.ok:
                return HttpResponse(status=r.status_code)

            return self.handle_esri_response(r)

        except:
            return HttpResponse(status=500)


class XLSView(View):
    def genXlsSheet(self):
        instance = Survey.objects.get()
        self

    model = Survey

def download_xls(request):
    filename = os.path.join(settings.BASE_DIR, f'QuestionLibrary\\generated_forms\\{Survey.objects.get(id=8)}.xlsx')
    content = FileWrapper(filename)
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = 'attachment; filename=%s' % 'whatever_name_will_appear_in_download.pdf'
    return response