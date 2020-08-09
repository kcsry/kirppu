# -*- coding: utf-8 -*-
import functools
import html
import io
from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse


def strip_generator(fn):
    @functools.wraps(fn)
    def inner(output, event, generator=False):
        if generator:
            # Return the generator object only when using StringIO.
            return fn(output, event)
        for _ in fn(output, event):
            pass

    return inner


def csv_streamer_view(request, generator, filename_base):
    debug = settings.DEBUG and request.GET.get("debug") is not None

    def streamer():
        if debug:
            yield "<!DOCTYPE html>\n<html>\n<body>\n<pre>"
        output = io.StringIO()
        for a_string in generator(output):
            val = output.getvalue()
            if debug:
                yield html.escape(val, quote=False)
            else:
                yield val
            output.truncate(0)
            output.seek(0)
        if debug:
            yield "</pre>\n</body>\n</html>"

    if debug:
        response = HttpResponse("".join(streamer()))
    else:
        response = StreamingHttpResponse(streamer(), content_type="text/plain; charset=utf-8")

    if request.GET.get("download") is not None:
        response["Content-Disposition"] = 'attachment; filename="%s.csv"' % quote(filename_base, safe="")
        response["Content-Type"] = "text/csv; charset=utf-8"
    return response
