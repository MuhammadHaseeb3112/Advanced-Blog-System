from django.contrib import admin
from django.templatetags.static import static as static_url
from django.urls import include, path, re_path
from django.shortcuts import redirect
from django.views.static import serve

from django.conf import settings
from django.conf.urls.static import static

from .views import home


urlpatterns = [

    path(
        'favicon.ico',
        lambda request: redirect(static_url('images/favicon.ico'), permanent=True)
    ),

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        '',
        home,
        name='home'
    ),

    path(
        'accounts/',
        include('accounts.urls')
    ),

    path(
        'accounts/',
        include('allauth.urls')
    ),

    path(
        'api/',
        include('api.urls')
    ),

    path(
        '',
        include('blog.urls')
    ),

]

# Uploaded files. static() only works with DEBUG on, so production (with
# SERVE_MEDIA=True, for a single-server deploy) serves them explicitly.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
