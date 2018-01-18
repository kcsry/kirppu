# -*- coding: utf-8 -*-
from django.urls import reverse

__author__ = 'codez'


class Api(object):
    def __init__(self, require_success):
        from kirppu.checkout_api import AJAX_FUNCTIONS

        def gen(method, view):
            url = reverse(view)

            def callback(client, *args, **kwargs):
                ret = getattr(client, method)(url, *args, **kwargs)
                if require_success and ret.status_code != 200:
                    raise AssertionError("Expected 200 OK, got {} / {}".format(
                        ret.status_code, ret.content.decode("utf-8")))
                return ret
            return callback

        self._end_points = {}
        for name, func in AJAX_FUNCTIONS.items():
            self._end_points[name] = gen(func.method.lower(), func.view)

    def __getattr__(self, function):
        if function == '__wrapped__':  # Placate inspect.is_wrapper
            return False
        return self._end_points[function]


api = Api(False)
api.__doc__ = "Checkout Api request handler."

apiOK = Api(True)
apiOK.__doc__ = "Checkout Api request handler that requires all calls to end 200 OK."
