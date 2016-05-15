from django.conf.urls import url

from .views import LoginView, CallbackView, LogoutView


urlpatterns = [
    url(r'^oauth2/login/?$', LoginView.as_view(), name='oauth2_login_view'),
    url(r'^oauth2/callback/?$', CallbackView.as_view(), name='oauth2_callback_view'),
    url(r'^oauth2/logout/?$', LogoutView.as_view(), name='oauth2_logout_view'),
]
