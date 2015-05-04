from __future__ import unicode_literals, print_function, absolute_import
from functools import wraps
import json

from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
)
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _i

from .models import (
    Clerk,
    Counter,
)

"""
Utility functions for writing AJAX views.
"""

# Some HTTP Status codes that are used here.
RET_BAD_REQUEST = 400  # Bad request
RET_UNAUTHORIZED = 401  # Unauthorized, though, not expecting Basic Auth...
RET_FORBIDDEN = 403     # Forbidden
RET_CONFLICT = 409  # Conflict
RET_AUTH_FAILED = 419  # Authentication timeout
RET_LOCKED = 423  # Locked resource


class AjaxError(Exception):
    def __init__(self, status, message='AJAX request failed'):
        super(AjaxError, self).__init__(message)
        self.status = status
        self.message = message

    def render(self):
        return HttpResponse(
            self.message,
            content_type='text/plain',
            status=self.status,
        )


class AjaxFunc(object):
    def __init__(self, func, url, method):
        self.name = func.__name__               # name of the view function
        self.url = url                          # url for url config
        self.view_name = 'api_' + self.name     # view name for url config
        self.view = 'kirppu:' + self.view_name  # view name for templates
        self.method = method                    # http method for templates


def ajax_func(url, register_func, method='POST', params=None):
    """
    Decorate the view function properly and register it.

    The decorated view will not be called if
        1. the request is not an AJAX request,
        2. the request method does not match the given method,
        OR
        3. the parameters are not present in the request data.

    If the decorated view raises an AjaxError, it will be rendered.

    :param url: Django url pattern of the AJAX function
    :type url: str
    :param register_func: Function to be called in order to register the
    AJAX function
    :type register_func: function with a single parameter of type AjaxFunc
    :param method: Required HTTP method; either 'GET' or 'POST'
    :type method: str
    :return: A decorator for a view function
    :rtype: function
    """
    params = params or []

    def decorator(func):
        # Register the function.
        register_func(AjaxFunc(func, url, method))

        # Decorate func.
        func = require_http_methods([method])(func)

        @wraps(func)
        def wrapper(request, **kwargs):
            if not request.is_ajax():
                return HttpResponseBadRequest("Invalid requester")

            # Pass request params to the view as keyword arguments.
            # The first argument is skipped since it is the request.
            request_data = request.GET if method == 'GET' else request.POST
            for param in params:
                try:
                    kwargs[param] = request_data[param]
                except KeyError:
                    return HttpResponseBadRequest()

            try:
                result = func(request, **kwargs)
            except AjaxError as ae:
                return ae.render()

            if isinstance(result, HttpResponse):
                return result
            else:
                return HttpResponse(
                    json.dumps(result),
                    status=200,
                    content_type='application/json',
                )
        return wrapper

    return decorator


def get_counter(request):
    """
    Get the Counter object associated with a request.

    Raise AjaxError if session is invalid or counter is not found.
    """
    if "counter" not in request.session:
        raise AjaxError(RET_UNAUTHORIZED, _i(u"Not logged in."))

    counter_id = request.session["counter"]
    try:
        counter_object = Counter.objects.get(pk=counter_id)
    except Counter.DoesNotExist:
        raise AjaxError(
            RET_UNAUTHORIZED,
            _i(u"Counter has gone missing."),
        )

    return counter_object


def get_clerk(request):
    """
    Get the Clerk object associated with a request.

    Raise AjaxError if session is invalid or clerk is not found.
    """
    for key in ["clerk", "clerk_token", "counter"]:
        if key not in request.session:
            raise AjaxError(RET_UNAUTHORIZED, _i(u"Not logged in."))

    clerk_id = request.session["clerk"]
    clerk_token = request.session["clerk_token"]

    try:
        clerk_object = Clerk.objects.get(pk=clerk_id)
    except Clerk.DoesNotExist:
        raise AjaxError(RET_UNAUTHORIZED, _i(u"Clerk not found."))

    if clerk_object.access_key != clerk_token:
        return AjaxError(RET_UNAUTHORIZED, _i(u"Bye."))

    return clerk_object


def require_counter_validated(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        get_counter(request)
        return func(request, *args, **kwargs)
    return wrapper


def require_clerk_login(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        get_clerk(request)
        return func(request, *args, **kwargs)
    return wrapper


def require_overseer_clerk_login(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        clerk = get_clerk(request)
        if not clerk.user.has_perm('kirppu.oversee'):
            raise AjaxError(RET_FORBIDDEN, _i(u"Access denied."))
        return func(request, *args, **kwargs)
    return wrapper
