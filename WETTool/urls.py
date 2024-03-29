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
from QuestionLibrary.views import EsriProxy, webhook
admin.site.site_header = 'WET Tool'

urlpatterns = [
    path(f'{settings.URL_PREFIX}webhook/', webhook),
    path(f'{settings.URL_PREFIX}oauth2/', include('social_django.urls', namespace='social_django')),
    path(f'{settings.URL_PREFIX}proxy/', EsriProxy.as_view()),
    path(f'{settings.URL_PREFIX}', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
