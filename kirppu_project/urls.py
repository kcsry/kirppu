from __future__ import unicode_literals, print_function, absolute_import
from django.conf.urls import include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

js_info_dict = {
    'packages': ('kirppu',),
}

urlpatterns = [
    url(r'^$', 'kirppu.views.index', name='home'),
    url(r'^kirppu/', include('kirppu.urls', app_name="kirppu", namespace="kirppu")),
    url(r'^accounts/', include('kirppuauth.urls', app_name="kirppuauth", namespace="kirppuauth")),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
]
