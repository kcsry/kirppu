from django.conf.urls import patterns, url
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import RedirectView

_urls = []


if not settings.KIRPPU_USE_SSO:
    _urls.append(url('^login/$', 'django.contrib.auth.views.login', name='local_login', kwargs={
        "template_name": "kirppuauth/login.html",
        "extra_context": {
            "ask_pass": True,
            "submit": lambda: reverse('kirppuauth:local_login'),
        },
    }))
    _urls.append(url('^profile/$', RedirectView.as_view(pattern_name="home")))
    _urls.append(url('^logout/$', 'django.contrib.auth.views.logout', name='local_logout', kwargs={
        "next_page": "home",
    }))


urlpatterns = patterns('', *_urls)
