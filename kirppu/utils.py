from __future__ import unicode_literals, print_function, absolute_import
import datetime
from functools import wraps
from django.conf import settings
from django.core.exceptions import PermissionDenied
import django.forms
from django.http.response import HttpResponseForbidden, HttpResponseBadRequest
from django.utils.translation import ugettext as _
from django.utils import timezone
import pytz

__author__ = 'jyrkila'

RFC8601DATETIME = "%Y-%m-%dT%H:%M:%S%z"
RFC8601DATE = "%Y-%m-%d"
TIME = "%H:%M:%S"
# RFC2822TIME = "%a, %d %b %Y %H:%M:%S %z"
MEM_TIMES = {}


from barcode.writer import BaseWriter, mm2px

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Could not find PIL.")
    PixelWriter = None
else:
    class PixelWriter(BaseWriter):
        # According to wikipedia 7x smallest unit width, but 10x according
        # to some other sources.
        _quiet_zone = 10

        @classmethod
        def quiet_zone(cls):
            """
            Get total quiet zone added by this writer.

            :return: Quiet zone amount.
            :rtype: int
            """
            return cls._quiet_zone * 2

        def __init__(self, format='PNG'):
            BaseWriter.__init__(self, self._init, self._paint_module,
                                self._paint_text, self._finish)
            self.format = format.lower()
            self.dpi = 300
            self._image = None
            self._draw = None

        def _init(self, code):
            size = self.calculate_size(len(code[0]), len(code), self.dpi)

            if self.format == 'gif':
                # Monochrome doesn't work with gifs for some reason.
                color_mode = 'L'
            else:
                color_mode = '1'

            self._image = Image.new(color_mode, size, 255)
            self._draw = ImageDraw.Draw(self._image)

        def _paint_module(self, xpos, ypos, width, color):
            xpos += self._quiet_zone
            xpos -= 2  # The position is off by this much for whatever reason.
            size = [xpos, 0, xpos + width, 0]
            self._draw.rectangle(size, outline=color, fill=color)

        def _paint_text(self, xpos, ypos):
            pass

        def _finish(self):
            return self._image

        def save(self, filename, output):
            filename = '{0}.{1}'.format(filename, self.format.lower())
            output.save(filename, self.format.upper())
            return filename

        def calculate_size(self, modules_per_line, number_of_lines, dpi=300):
            width = modules_per_line * self.module_width
            width += 2 * self._quiet_zone  # quiet zone

            height = 1

            return width, height


def model_dict_fn(*args, **kwargs):
    """
    Return a function that will create dictionary by reading values from class instance.

        >>> class C(object):
        ...     def __init__(self):
        ...         self.a = 3
        ...     as_dict = model_dict_fn("a")
        ...     as_renamed = model_dict_fn(renamed="a")
        ...     as_called = model_dict_fn(multi=lambda self: self.a * 2)
        >>> C().as_dict(), C().as_renamed(), C().as_called()
        ({'a': 3}, {'renamed': 3}, {'multi': 6})

    :param args: List of fields.
    :param kwargs: Fields to be renamed or overridden with another function call.
    :return: Function.
    """
    fields = {}
    for plain_key in args:
        fields[plain_key] = plain_key
    fields.update(kwargs)

    def model_dict(self):
        """
        Get model fields as dictionary (for JSON/AJAX usage). Fields returned:
        {0}
        """
        ret = {}
        for key, value in fields.items():
            if callable(value):
                ret[key] = value(self)
            elif value is None:
                if value in ret:
                    del ret[value]
            else:
                ret[key] = getattr(self, value)
                if callable(ret[key]):
                    ret[key] = ret[key]()
        return ret
    model_dict.__doc__ = model_dict.__doc__.format(", ".join(fields.keys()))
    return model_dict


def format_datetime(dt):
    """
    Format given datetime in RFC8601 format, that is used with moment.js.

    :param dt: Datetime to format.
    :type dt: datetime.datetime|datetime.date|datetime.time
    :return: Formatted string.
    :rtype: str
    :raises RuntimeError: If input type is not understood.
    """
    if isinstance(dt, datetime.datetime):
        result = dt.strftime(RFC8601DATETIME)
    elif isinstance(dt, datetime.date):
        result = dt.strftime(RFC8601DATE)
    elif isinstance(dt, datetime.time):
        result = dt.strftime(TIME)
    else:
        raise RuntimeError("Unsupported object given for format_datetime: " + repr(dt))
    return result


class StaticTextWidget(django.forms.widgets.Widget):
    """
    Static text-field widget. Text should be set with set_text().
    Otherwise `initial`-text is used, or empty string as fallback.
    The resulting text is rendered instead of any widget.
    """
    def __init__(self, **kwargs):
        super(StaticTextWidget, self).__init__(**kwargs)
        self._static_text = None

    def set_text(self, text):
        self._static_text = text

    def has_text(self):
        return self._static_text is not None

    def render(self, name, value, attrs=None):
        return self._static_text or value or u""


class ButtonWidget(StaticTextWidget):
    def __init__(self, **kwargs):
        self._click = kwargs.pop("click", None)
        super(ButtonWidget, self).__init__(**kwargs)

    def set_click(self, click):
        self._click = click

    def render(self, name, value, attrs=None):
        from django.utils.html import format_html
        from django.utils.encoding import force_text

        return format_html(u'<button type="button" onclick="{0}">{1}</button>'.format(
            self._click,
            force_text(self._static_text or value or u""),
        ))


class StaticText(django.forms.CharField):
    """
    Static text-field using StaticTextWidget. Only required parameter is `text`.
    Other parameters as per `CharField`.
    """
    def __init__(self, text, **kwargs):
        kwargs.setdefault("widget", StaticTextWidget)
        kwargs["required"] = False
        super(StaticText, self).__init__(**kwargs)

        if isinstance(self.widget, StaticTextWidget) and not self.widget.has_text():
            self.widget.set_text(text)


def require_setting(setting, value):
    """
    Decorator that requires a setting in settings to be a certain value before continuing to the view.

    :param setting: Setting key to find from settings.
    :type setting: str
    :param value: Accepted value, or one-argument callable returning True if accepted and False otherwise.
    :type value: T | callable
    :return: View decorator that will test the specified setting.
    """
    def decorator(fn):
        from django.conf import settings
        callback = callable(value)

        @wraps(fn)
        def inner(request, *args, **kwargs):
            current_value = getattr(settings, setting, None)
            if not ((not callback and current_value == value) or (callback and value(current_value))):
                raise PermissionDenied()
            return fn(request, *args, **kwargs)
        return inner
    return decorator


def is_now_after(date_str):
    """
    Check if the current time is after given datetime string.
    The string must be in "YYYY-MM-DD HH:MM:SS" format and it is expected to be in settings.TIME_ZONE timezone.

    Parsed date_str values are cached in MEM_TIMES, so this function is not suitable for testing random user inputs.

    :param date_str: Instant to test against.
    :type date_str: str
    :return: True if current time is after the given datetime. False if not.
    """
    cached_instant = MEM_TIMES.get(date_str)
    if cached_instant is None:
        naive = timezone.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        if settings.USE_TZ:
            cached_instant = pytz.timezone(settings.TIME_ZONE).localize(naive)
        else:
            cached_instant = naive
        MEM_TIMES[date_str] = cached_instant

    return timezone.now() > cached_instant


def is_vendor_open():
    """
    Test if Item edit for vendor is currently open.

    :return: True if open, False if not and modifications by vendor must not be allowed.
    """
    return not is_now_after(settings.KIRPPU_REGISTER_ACTIVE_UNTIL)


def require_vendor_open(fn):
    """
    Decorate (view) function so that it will return Forbidden if Item edit for vendor is not open.

    :param fn: Function to decorate.
    :return: Decorated function.
    """
    @wraps(fn)
    def inner(*args, **kwargs):
        if not is_vendor_open():
            return HttpResponseForbidden(_(u"Registration is closed"))
        return fn(*args, **kwargs)
    return inner


def require_test(test):
    """
    Decorate view function so that it will return Forbidden if given test does not return True when called.

    :param test: Test function. It will be called with `request` argument.
    :type test: callable
    :return: Decorated function.
    """
    def wrapper(fn):
        @wraps(fn)
        def inner(request, *args, **kwargs):
            if not test(request):
                raise PermissionDenied()
            return fn(request, *args, **kwargs)
        return inner
    return wrapper


def barcode_view(fn):
    """
    Decorator for views that render bar-codes. This will select image format, and on failure, return BadRequest.

    :param fn: Function to decorate. Function will get extra keyword argument `bar_type` containing the image format
        name.
    :return: Decorated function.
    """
    @wraps(fn)
    def inner(request, *args, **kwargs):
        # Use PNG if we can because SVGs from pyBarcode are huge.
        default_format = 'png' if PixelWriter else 'svg'
        bar_type = request.GET.get("format", default_format).lower()

        if bar_type not in ('svg', 'png', 'gif', 'bmp'):
            return HttpResponseBadRequest(_(u"Image extension not supported"))

        kwargs["bar_type"] = bar_type
        return fn(request, *args, **kwargs)
    return inner
