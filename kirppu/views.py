from __future__ import unicode_literals, print_function, absolute_import
from collections import namedtuple
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
import django.urls as url
from django.db import transaction, models
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.http import Http404
from django.shortcuts import (
    redirect,
    render,
    get_object_or_404,
)
from django.utils import timezone
from django.utils.formats import localize
from django.utils.six import string_types
from django.utils.translation import ugettext as _
from django.views.csrf import csrf_failure as django_csrf_failure
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.generic import RedirectView

from .checkout_api import clerk_logout_fn
from . import ajax_util
from .forms import ItemRemoveForm, VendorItemForm, VendorBoxForm
from .fields import ItemPriceField
from .models import (
    Box,
    Clerk,
    Item,
    ItemType,
    Vendor,
    UserAdapter,
    UIText,
    Receipt,
)
from .stats import ItemCountData, ItemEurosData
from .util import get_form
from .utils import (
    barcode_view,
    is_vendor_open,
    require_setting,
    require_test,
    require_vendor_open,
)
from .templatetags.kirppu_tags import get_dataurl
from .vendors import get_multi_vendor_values
import pubcode


def index(request):
    return redirect("kirppu:vendor_view")


class MobileRedirect(RedirectView):
    permanent = False
    pattern_name = "kirppu:mobile"


@login_required
@require_http_methods(["POST"])
@require_vendor_open
def item_add(request):
    if not Vendor.has_accepted(request):
        return HttpResponseBadRequest()
    vendor = Vendor.get_or_create_vendor(request)
    form = VendorItemForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.get_any_error())

    item_cnt = Item.objects.filter(vendor=vendor).count()

    # Create the items and construct a response containing all the items that have been added.
    response = []
    max_items = settings.KIRPPU_MAX_ITEMS_PER_VENDOR
    data = form.db_values()
    name = data.pop("name")

    for suffix in form.cleaned_data["suffixes"]:
        if item_cnt >= max_items:
            error_msg = _(u"You have %(max_items)s items, which is the maximum. No more items can be registered.")
            return HttpResponseBadRequest(error_msg % {'max_items': max_items})
        item_cnt += 1

        suffixed_name = (name + u" " + suffix).strip() if suffix else name
        item = Item.new(
            name=suffixed_name,
            vendor=vendor,
            **data
        )
        item_dict = item.as_public_dict()
        item_dict['barcode_dataurl'] = get_dataurl(item.code, 'png')
        response.append(item_dict)

    return HttpResponse(json.dumps(response), 'application/json')


@login_required
@require_http_methods(["POST"])
def item_hide(request, code):
    vendor = Vendor.get_vendor(request)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)

    item.hidden = True
    item.save()

    return HttpResponse()


@login_required
@require_http_methods(['POST'])
def item_to_not_printed(request, code):
    vendor = Vendor.get_vendor(request)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor, box__isnull=True)

    if settings.KIRPPU_COPY_ITEM_WHEN_UNPRINTED:
        # Create a duplicate of the item with a new code and hide the old item.
        # This way, even if the user forgets to attach the new tags, the old
        # printed tag is still in the system.
        if not is_vendor_open(request):
            return HttpResponseForbidden("Registration is closed")

        new_item = Item.new(
            name=item.name,
            price=item.price,
            vendor=item.vendor,
            type=item.type,
            state=Item.ADVERTISED,
            itemtype=item.itemtype,
            adult=item.adult
        )
        item.hidden = True
    else:
        item.printed = False
        new_item = item
    item.save()

    item_dict = {
        'vendor_id': new_item.vendor_id,
        'code': new_item.code,
        'barcode_dataurl': get_dataurl(item.code, 'png'),
        'name': new_item.name,
        'price': str(new_item.price).replace('.', ','),
        'type': new_item.type,
        'adult': new_item.adult,
    }

    return HttpResponse(json.dumps(item_dict), 'application/json')


@login_required
@require_http_methods(["POST"])
def item_to_printed(request, code):
    vendor = Vendor.get_vendor(request)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor, box__isnull=True)

    item.printed = True
    item.save()

    return HttpResponse()


@login_required
@require_http_methods(["POST"])
@require_vendor_open
def item_update_price(request, code):
    try:
        price = ItemPriceField().clean(request.POST.get('value'))
    except ValidationError as error:
        return HttpResponseBadRequest(u' '.join(error.messages))

    vendor = Vendor.get_vendor(request)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor, box__isnull=True)

    if item.is_locked():
        return HttpResponseBadRequest("Item has been brought to event. Price can't be changed.")

    item.price = str(price)
    item.save()

    return HttpResponse(str(price).replace(".", ","))


@login_required
@require_http_methods(["POST"])
@require_vendor_open
def item_update_name(request, code):
    name = request.POST.get("value", "no name")

    name = name[:80]

    vendor = Vendor.get_vendor(request)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)

    if item.is_locked():
        return HttpResponseBadRequest("Item has been brought to event. Name can't be changed.")

    item.name = name
    item.save()

    return HttpResponse(name)


@login_required
@require_http_methods(["POST"])
def item_update_type(request, code):
    tag_type = request.POST.get("tag_type", None)

    vendor = Vendor.get_vendor(request)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)
    item.type = tag_type
    item.save()
    return HttpResponse()


@login_required
@require_http_methods(["POST"])
def all_to_print(request):
    vendor = Vendor.get_vendor(request)
    items = Item.objects.filter(vendor=vendor).filter(printed=False).filter(box__isnull=True)

    items.update(printed=True)

    return HttpResponse()


@login_required
@require_http_methods(["POST"])
@require_vendor_open
def box_add(request):
    if not Vendor.has_accepted(request):
        return HttpResponseBadRequest()
    vendor = Vendor.get_vendor(request)
    form = VendorBoxForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.get_any_error())

    data = form.db_values()

    # Verify that user doesn't exceed his/hers item quota with the box.
    max_items = settings.KIRPPU_MAX_ITEMS_PER_VENDOR
    item_cnt = Item.objects.filter(vendor=vendor).count()
    count = data["count"]
    if item_cnt >= max_items:
        error_msg = _(u"You have %(max_items)s items, which is the maximum. No more items can be registered.")
        return HttpResponseBadRequest(error_msg % {'max_items': max_items})
    elif max_items < count + item_cnt:
        error_msg = _(u"You have %(item_cnt)s items. "
                      u"Creating this box would cause the items to exceed the maximum number of allowed items.")
        return HttpResponseBadRequest(error_msg % {'item_cnt': item_cnt})

    # Create the box and items. and construct a response containing box and all the items that have been added.
    box = Box.new(
        vendor=vendor,
        **data
    )

    box_dict = box.as_public_dict()
    box_dict["vendor_id"] = vendor.id

    return render(request, "kirppu/app_boxes_box.html", box_dict)


@login_required
@require_http_methods(["POST"])
def box_hide(request, box_id):

    with transaction.atomic():

        vendor = Vendor.get_vendor(request)
        box = get_object_or_404(Box.objects, id=box_id)
        box_vendor = box.get_vendor()
        if box_vendor.id != vendor.id:
            raise Http404()

        box.set_hidden(True)

    return HttpResponse()


@login_required
@require_http_methods(["POST"])
def box_print(request, box_id):

    with transaction.atomic():

        vendor = Vendor.get_vendor(request)
        box = get_object_or_404(Box.objects, id=box_id)
        box_vendor = box.get_vendor()
        if box_vendor.id != vendor.id:
            raise Http404()

        box.set_printed(True)

    return HttpResponse()


@login_required
@require_http_methods(["GET"])
@barcode_view
def box_content(request, box_id, bar_type):

    """
    Get a page containing the contents of one box for printing

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :param bar_type: Image type of the generated bar. See `kirppu_tags.barcode_dataurl`.
    :type bar_type: str
    :return: HttpResponse or HttpResponseBadRequest
    """

    vendor = Vendor.get_vendor(request)
    boxes = Box.objects.filter(id=box_id, item__vendor=vendor, item__hidden=False).distinct()
    if boxes.count() == 0:
        raise Http404()
    box = boxes[0]
    item = box.get_representative_item()

    render_params = {
        'box': box,
        'item': item,
        'bar_type': bar_type,
        'CURRENCY': settings.KIRPPU_CURRENCY,
    }

    return render(request, "kirppu/app_boxes_content.html", render_params)


def _vendor_menu_contents(request):
    """
    Generate menu for Vendor views.
    Returned tuple contains entries for the menu, each entry containing a
    name, url, and flag indicating whether the entry is currently active
    or not.

    :param request: Current request being processed.
    :return: List of menu items containing name, url and active fields.
    :rtype: tuple[MenuItem,...]
    """
    active = request.resolver_match.view_name
    menu_item = namedtuple("MenuItem", "name url active sub_items")

    def fill(name, func, sub=None):
        return menu_item(name, url.reverse(func) if func else None, func == active, sub)

    items = [
        fill(_(u"Home"), "kirppu:vendor_view"),
        fill(_(u"Item list"), "kirppu:page"),
        fill(_(u"Box list"), "kirppu:vendor_boxes"),
    ]

    try:
        # FIXME: Implement a better way to enable the link. db-options...
        login_text = UIText.objects.get(identifier="mobile_login")
        if "--enable--" in login_text.text:
            items.append(fill(_("Mobile"), "kirppu:mobile"))
    except UIText.DoesNotExist:
        pass

    manage_sub = []
    if request.user.is_staff or UserAdapter.is_clerk(request.user):
        manage_sub.append(fill(_(u"Checkout commands"), "kirppu:commands"))
        if settings.KIRPPU_CHECKOUT_ACTIVE:
            manage_sub.append(fill(_(u"Checkout"), "kirppu:checkout_view"))
            manage_sub.append(fill(_("Box codes"), "kirppu:box_codes"))

    if request.user.is_staff:
        manage_sub.append(fill(_(u"Clerk codes"), "kirppu:clerks"))
        manage_sub.append(fill(_(u"Lost and Found"), "kirppu:lost_and_found"))

    if request.user.is_staff or UserAdapter.is_clerk(request.user):
        manage_sub.append(fill(_(u"Statistics"), "kirppu:stats_view"))

    if request.user.is_staff:
        try:
            manage_sub.append(fill(_(u"Site administration"), "admin:index"))
        except url.NoReverseMatch as e:
            pass

    if manage_sub:
        items.append(fill(_(u"Management"), "", manage_sub))
    return items


@login_required
@require_http_methods(["GET"])
@barcode_view
def get_items(request, bar_type):
    """
    Get a page containing all items for vendor.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :return: HttpResponse or HttpResponseBadRequest
    """

    user = request.user
    if user.is_staff and "user" in request.GET:
        user = get_object_or_404(get_user_model(), username=request.GET["user"])

    vendor = Vendor.get_vendor(request)

    vendor_data = get_multi_vendor_values(request)
    if settings.KIRPPU_MULTIPLE_VENDORS_PER_USER and user.is_staff and "user" in request.GET:
        raise NotImplementedError  # FIXME: Decide how this should work.

    vendor_items = Item.objects.filter(vendor=vendor, hidden=False, box__isnull=True)
    items = vendor_items.filter(printed=False)
    printed_items = vendor_items.filter(printed=True)

    # Order from newest to oldest, because that way new items are added
    # to the top and the user immediately sees them without scrolling
    # down.
    items = items.order_by('-id')

    item_name_placeholder = UIText.get_text("item_placeholder", _("Ranma ½ Vol."))

    render_params = {
        'items': items,
        'printed_items': printed_items,
        'bar_type': bar_type,
        'item_name_placeholder': item_name_placeholder,

        'profile_url': settings.PROFILE_URL,
        'terms_accepted': vendor.terms_accepted if vendor is not None else False,

        'is_registration_open': is_vendor_open(request),
        'is_registration_closed_for_users': not is_vendor_open(),
        'menu': _vendor_menu_contents(request),
        'itemTypes': ItemType.as_tuple(),
        'CURRENCY': settings.KIRPPU_CURRENCY,
        'PRICE_MIN_MAX': settings.KIRPPU_MIN_MAX_PRICE,
    }
    render_params.update(vendor_data)

    return render(request, "kirppu/app_items.html", render_params)


@login_required
@require_http_methods(["GET"])
def get_boxes(request):
    """
    Get a page containing all boxes for vendor.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :return: HttpResponse or HttpResponseBadRequest
    """

    user = request.user
    if user.is_staff and "user" in request.GET:
        user = get_object_or_404(get_user_model(), username=request.GET["user"])

    vendor = Vendor.get_vendor(request)
    vendor_data = get_multi_vendor_values(request)

    boxes = Box.objects.filter(item__vendor=vendor, item__hidden=False).distinct()

    # Order from newest to oldest, because that way new boxes are added
    # to the top and the user immediately sees them without scrolling
    # down.
    boxes = boxes.order_by('-id')

    box_name_placeholder = UIText.get_text("box_placeholder", _("Box full of Ranma"))

    render_params = {
        'boxes': boxes,
        'box_name_placeholder': box_name_placeholder,

        'profile_url': settings.PROFILE_URL,
        'terms_accepted': vendor.terms_accepted if vendor is not None else False,

        'is_registration_open': is_vendor_open(request),
        'is_registration_closed_for_users': not is_vendor_open(),
        'menu': _vendor_menu_contents(request),
        'itemTypes': ItemType.as_tuple(),
        'CURRENCY': settings.KIRPPU_CURRENCY,
        'PRICE_MIN_MAX': settings.KIRPPU_MIN_MAX_PRICE,
    }
    render_params.update(vendor_data)

    return render(request, "kirppu/app_boxes.html", render_params)


@login_required
@require_test(lambda request: request.user.is_staff)
@barcode_view
def get_clerk_codes(request, bar_type):
    items = []
    code_item = namedtuple("CodeItem", "name code")

    for c in Clerk.objects.filter(access_key__isnull=False):
        if not c.is_valid_code:
            continue
        code = c.get_code()
        if c.user is not None:
            name = c.user.get_short_name()
            if len(name) == 0:
                name = c.user.get_username()
        else:
            name = ""

        items.append(code_item(name=name, code=code))

    if items:
        # Generate a code to check it's length.
        name, code = items[0]
        width = pubcode.Code128(code, charset='B').width(add_quiet_zone=True)
    else:
        width = None  # Doesn't matter.

    return render(request, "kirppu/app_clerks.html", {
        'items': items,
        'bar_type': bar_type,
        'repeat': range(1),
        'barcode_width': width,
    })


@login_required
@require_test(lambda request: request.user.is_staff or UserAdapter.is_clerk(request.user))
@barcode_view
def get_counter_commands(request, bar_type):
    return render(request, "kirppu/app_commands.html", {
        'title': _(u"Counter commands"),
    })


@login_required
@require_test(lambda request: request.user.is_staff or UserAdapter.is_clerk(request.user))
@barcode_view
def get_boxes_codes(request, bar_type):
    boxes = Box.objects.filter(box_number__isnull=False).order_by("box_number")
    vm = []
    for box in boxes:
        code = "box%d" % box.box_number
        img = pubcode.Code128(code, charset='B').data_url(image_format=bar_type, add_quiet_zone=True)
        r = box.get_representative_item()  # type: Item

        vm.append({
            "name": box.description,
            "code": code,
            "data_url": img,
            "adult": r.adult,
            "vendor_id": r.vendor_id,
            "price": r.price_fmt,
            "bundle_size": box.bundle_size,
            "box_number": box.box_number,
        })

    return render(request, "kirppu/boxes_list.html", {
        "bar_type": bar_type,
        "boxes": vm
    })


# Access control by settings.
# CSRF is not generated if the Checkout-mode is not activated in settings.
@require_setting("KIRPPU_CHECKOUT_ACTIVE", True)
@ensure_csrf_cookie
def checkout_view(request):
    """
    Checkout view.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :return: Response containing the view.
    :rtype: HttpResponse
    """
    clerk_logout_fn(request)
    context = {
        'CURRENCY': settings.KIRPPU_CURRENCY,
        'PURCHASE_MAX': settings.KIRPPU_MAX_PURCHASE,
    }
    if settings.KIRPPU_AUTO_CLERK and settings.DEBUG:
        if isinstance(settings.KIRPPU_AUTO_CLERK, string_types):
            real_clerks = Clerk.objects.filter(user__username=settings.KIRPPU_AUTO_CLERK)
        else:
            real_clerks = Clerk.objects.filter(user__isnull=False)
        for clerk in real_clerks:
            if clerk.is_enabled:
                context["auto_clerk"] = clerk.get_code()
                break

    return render(request, "kirppu/app_checkout.html", context)


@require_setting("KIRPPU_CHECKOUT_ACTIVE", True)
@ensure_csrf_cookie
def overseer_view(request):
    """Overseer view."""
    try:
        ajax_util.require_user_features(counter=True, clerk=True, overseer=True)(lambda _: None)(request)
    except ajax_util.AjaxError:
        return redirect('kirppu:checkout_view')
    else:
        context = {
            'itemtypes': ItemType.as_tuple(),
            'itemstates': Item.STATE,
            'CURRENCY': settings.KIRPPU_CURRENCY,
        }
        return render(request, 'kirppu/app_overseer.html', context)


@ensure_csrf_cookie
def stats_view(request):
    """Stats view."""
    try:
        ajax_util.require_user_features(counter=True, clerk=True, staff_override=True)(lambda _: None)(request)
    except ajax_util.AjaxError:
        if settings.KIRPPU_CHECKOUT_ACTIVE:
            return redirect('kirppu:checkout_view')
        else:
            raise PermissionDenied()

    ic = ItemCountData(ItemCountData.GROUP_ITEM_TYPE)
    ie = ItemEurosData(ItemEurosData.GROUP_ITEM_TYPE)
    sum_name = _("Sum")
    item_types = ItemType.objects.order_by("order").values_list("id", "title")

    number_of_items = [
        ic.data_set(item_type, type_name)
        for item_type, type_name in item_types
    ]
    number_of_items.append(ic.data_set("sum", sum_name))

    number_of_euros = [
        ie.data_set(item_type, type_name)
        for item_type, type_name in item_types
    ]
    number_of_euros.append(ie.data_set("sum", sum_name))

    vendor_item_data_counts = []
    vendor_item_data_euros = []
    vic = ItemCountData(ItemCountData.GROUP_VENDOR)
    vie = ItemEurosData(ItemEurosData.GROUP_VENDOR)
    vie.use_cents = True
    vendor_item_data_row_size = 0

    for vendor_id in vic.keys():
        name = _("Vendor %i") % vendor_id
        counts = vic.data_set(vendor_id, name)
        euros = vie.data_set(vendor_id, name)
        if vendor_item_data_row_size == 0:
            vendor_item_data_row_size = len(list(counts.property_names))

        vendor_item_data_counts.append(counts)
        vendor_item_data_euros.append(euros)

    context = {
        'number_of_items': number_of_items,
        'number_of_euros': number_of_euros,
        'vendor_item_data_counts': vendor_item_data_counts,
        'vendor_item_data_euros': vendor_item_data_euros,
        'vendor_item_data_row_size': vendor_item_data_row_size,
        'checkout_active': settings.KIRPPU_CHECKOUT_ACTIVE,
        'CURRENCY': settings.KIRPPU_CURRENCY["raw"],
    }

    return render(request, 'kirppu/app_stats.html', context)


@ensure_csrf_cookie
def type_stats_view(request, type_id):
    try:
        ajax_util.require_user_features(counter=True, clerk=True, staff_override=True)(lambda _: None)(request)
    except ajax_util.AjaxError:
        if settings.KIRPPU_CHECKOUT_ACTIVE:
            return redirect('kirppu:checkout_view')
        else:
            raise PermissionDenied()

    item_type = get_object_or_404(ItemType, id=int(type_id))

    return render(request, "kirppu/type_stats.html", {
        "type_id": item_type.id,
        "type_title": item_type.title,
    })


def _float_array(array):
    # noinspection PyPep8Naming
    INFINITY = float('inf')

    def _float(f):
        if f != f:
            return "NaN"
        elif f == INFINITY:
            return 'Infinity'
        elif f == -INFINITY:
            return '-Infinity'
        return float.__repr__(f)

    line_length = 20

    o = [
        ", ".join(_float(e) for e in array[i:i + line_length])
        for i in range(0, len(array), line_length)
    ]

    return "[\n" + ",\n".join(o) + "]"


@ensure_csrf_cookie
def statistical_stats_view(request):
    brought_states = (Item.BROUGHT, Item.STAGED, Item.SOLD, Item.COMPENSATED, Item.RETURNED)

    registered = Item.objects.count()
    brought = Item.objects.filter(state__in=brought_states).count()
    sold = Item.objects.filter(state__in=(Item.STAGED, Item.SOLD, Item.COMPENSATED)).count()

    general = {
        "registered": registered,
        "deleted": Item.objects.filter(hidden=True).count(),
        "brought": brought,
        "broughtOfRegistered": (brought * 100.0 / registered) if registered > 0 else 0,
        "sold": sold,
        "soldOfBrought": (sold * 100.0 / brought) if brought > 0 else 0,
        "vendors": Vendor.objects.filter(item__state__in=brought_states).distinct().count(),
        "vendorsTotal": Vendor.objects.count(),
    }

    compensations = Vendor.objects.filter(item__state=Item.COMPENSATED) \
        .annotate(v_sum=models.Sum("item__price")).order_by("v_sum").values_list("v_sum", flat=True)
    compensations = [float(e) for e in compensations]

    purchases = list(
        Receipt.objects.filter(status=Receipt.FINISHED, type=Receipt.TYPE_PURCHASE)
        .order_by("total")
        .values_list("total", flat=True)
    )
    purchases = [float(e) for e in purchases]

    return render(request, "kirppu/general_stats.html", {
        "compensations": _float_array(compensations),
        "purchases": _float_array(purchases),
        "checkout_active": settings.KIRPPU_CHECKOUT_ACTIVE,
        "general": general,
        "CURRENCY": settings.KIRPPU_CURRENCY["raw"],
    })


def vendor_view(request):
    """
    Render main view for vendors.

    :rtype: HttpResponse
    """
    user = request.user

    vendor_data = get_multi_vendor_values(request)
    if user.is_authenticated:
        vendor = Vendor.get_vendor(request)
        items = Item.objects.filter(vendor=vendor, hidden=False, box__isnull=True)
        boxes = Box.objects.filter(item__vendor=vendor, item__hidden=False).distinct()
        boxed_items = Item.objects.filter(vendor=vendor, hidden=False, box__isnull=False)
    else:
        vendor = None
        items = []
        boxes = []
        boxed_items = Item.objects.none()

    context = {
        'user': user,
        'items': items,

        'total_price': sum(i.price for i in items),
        'num_total': len(items),
        'num_printed': len(list(filter(lambda i: i.printed, items))),

        'boxes': boxes,
        'boxes_count': len(boxes),
        'boxes_total_price': boxed_items.aggregate(sum=models.Sum("price"))["sum"],
        'boxes_item_count': boxed_items.count(),
        'boxes_printed': len(list(filter(lambda i: i.is_printed(), boxes))),

        'profile_url': settings.PROFILE_URL,
        'menu': _vendor_menu_contents(request),
        'CURRENCY': settings.KIRPPU_CURRENCY,
    }
    context.update(vendor_data)
    return render(request, "kirppu/app_frontpage.html", context)


@login_required
@require_http_methods(["POST"])
def accept_terms(request):
    vendor = Vendor.get_or_create_vendor(request)
    if vendor.terms_accepted is None:
        vendor.terms_accepted = timezone.now()
        vendor.save()

    result = timezone.template_localtime(vendor.terms_accepted)
    result = localize(result)

    return HttpResponse(json.dumps({
        "result": "ok",
        "time": result,
    }), "application/json")


@login_required
def remove_item_from_receipt(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    form = get_form(ItemRemoveForm, request)

    if request.method == "POST" and form.is_valid():
        form.save(request)
        return HttpResponseRedirect(url.reverse('kirppu:remove_item_from_receipt'))

    return render(request, "kirppu/app_item_receipt_remove.html", {
        'form': form,
    })


@login_required
@require_test(lambda request: request.user.is_staff)
def lost_and_found_list(request):
    items = Item.objects.select_related("vendor").filter(lost_property=True, abandoned=False).order_by("vendor", "name")

    vendor_object = namedtuple("VendorItems", "vendor vendor_id items")

    vendor_list = {}
    for item in items:
        vendor_id = item.vendor_id
        if vendor_id not in vendor_list:
            vendor_list[vendor_id] = vendor_object(item.vendor.user, item.vendor_id, [])

        vendor_list[vendor_id].items.append(item)

    return render(request, "kirppu/lost_and_found.html", {
        'menu': _vendor_menu_contents(request),
        'items': vendor_list,
    })


def kirppu_csrf_failure(request, reason=""):
    if request.is_ajax() or request.META.get("HTTP_ACCEPT", "") == "text/json":
        # TODO: Unify the response to match requested content type.
        return HttpResponseForbidden(
            _("CSRF verification failed. Request aborted."),
            content_type="text/plain; charset=utf-8",
        )
    else:
        return django_csrf_failure(request, reason=reason)
