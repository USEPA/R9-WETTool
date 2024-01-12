"""WETTool URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from rest_framework import routers
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import ensure_csrf_cookie
from QuestionLibrary.views import *
admin.site.site_header = 'WET Tool'


api_router = routers.DefaultRouter()
api_router.register(r'lookup_group', LookupGroupViewSet)
api_router.register(r'lookup', LookupViewSet)
api_router.register(r'media', MediaViewSet)
api_router.register(r'epa_response', EPAResponseViewSet)
api_router.register(r'facility_type', FacilityTypeViewSet)
api_router.register(r'category_type', CategoryViewSet)
api_router.register(r'survey123_field_type', Survey123FieldTypeViewSet)
api_router.register(r'units', UnitViewSet)
api_router.register(r'esri_field_types', ESRIFieldTypesViewSet)
api_router.register(r'question', MasterQuestionViewSet)
api_router.register(r'survey', SurveyViewSet)
api_router.register(r'question_set', QuestionSetViewSet)
api_router.register(r'question_list', QuestionListViewSet)
api_router.register(r'survey_response', SurveyResponseViewSet)
api_router.register(r'related_question_list', RelatedQuestionListViewSet)
api_router.register(r'dashboard', DashboardViewSet)

@ensure_csrf_cookie
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    permissions = []
    groups = []
    for permission in request.user.user_permissions.all():
        permissions.append(permission.codename)
    for group in request.user.groups.all():
        groups.append(group.name)
        for permission in group.permissions.all():
            permissions.append(permission.codename)

    current_user = {
        'name': '{} {}'.format(request.user.first_name,
                               request.user.last_name) if request.user.first_name else request.user.username,
        'permissions': set(permissions),
        'is_superuser': request.user.is_superuser,
        'groups': set(groups)
    }
    return Response(current_user)

urlpatterns = [
    path(f'{settings.URL_PREFIX}webhook/', webhook),
    path(f'{settings.URL_PREFIX}oauth2/', include('social_django.urls', namespace='social_django')),
    path(f'{settings.URL_PREFIX}proxy/', EsriProxy.as_view()),
    path(f'{settings.URL_PREFIX}admin/', admin.site.urls),

    path(f'{settings.URL_PREFIX}api/', include(api_router.urls)),
    path(f'{settings.URL_PREFIX}api/current_user/', current_user),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

# urlpatterns += api_router.urls

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
