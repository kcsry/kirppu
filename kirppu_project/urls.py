from __future__ import unicode_literals, print_function, absolute_import
from django.conf.urls import include, url
from django.views.i18n import javascript_catalog

from kirppu.views import index

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

js_info_dict = {
    'packages': ('kirppu',),
}

urlpatterns = [
    url(r'^$', index, name='home'),
    url(r'^kirppu/', include('kirppu.urls', app_name="kirppu", namespace="kirppu")),
    url(r'^accounts/', include('kirppuauth.urls', app_name="kirppuauth", namespace="kirppuauth")),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict),
    url(r'^', include('kompassi_oauth2.urls')),
]
