from __future__ import unicode_literals, print_function, absolute_import
import random
from decimal import Decimal
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import MinLengthValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import F, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.module_loading import import_string
from django.utils.six import text_type, PY3
from django.conf import settings

from .utils import model_dict_fn, format_datetime, short_description

from .util import (
    number_to_hex,
    hex_to_number,
    b32_encode,
    b32_decode,
    pack,
    unpack,
    shorten_text,
)

if PY3:
    long = int

# Settings safety check.
if settings.KIRPPU_AUTO_CLERK and not settings.DEBUG:
    raise ImproperlyConfigured("Automatic clerk code usage may not be used in production!")

User = settings.AUTH_USER_MODEL


def decimal_to_transport(value):
    return long(value * Item.FRACTION)


class UserAdapterBase(object):
    """
    Base version of UserAdapter. This can be (optionally) subclassed somewhere else which can then be set
    to be used by system via `settings.KIRPPU_USER_ADAPTER`.
    """
    @classmethod
    def phone(cls, user):
        return user.phone

    @classmethod
    def phone_query(cls, rhs, fn=None):
        fn = "" if fn is None else ("__" + fn)
        return {"phone" + fn: rhs}

    @classmethod
    def is_clerk(cls, user, event):
        return hasattr(user, "clerk_set") and user.clerk_set.filter(event=event).exists()

    @classmethod
    def print_name(cls, user):
        last_name_part = user.last_name[:1]
        if last_name_part and last_name_part != user.last_name:
            last_name_part += "."
        name = u"{0} {1}".format(user.first_name, last_name_part).strip()
        if len(name) == 0:
            return user.username
        return name.title()

    @classmethod
    def full_name(cls, user):
        return user.get_full_name()


# The actual class is found by string in settings.
UserAdapter = import_string(settings.KIRPPU_USER_ADAPTER)


@python_2_unicode_compatible
class Person(models.Model):
    """
    Abstract person that is not User.
    """
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    phone = models.CharField(max_length=64, blank=True, null=False)

    def full_name(self):
        return u"{first_name} {last_name}".format(first_name=self.first_name, last_name=self.last_name).strip()

    def __str__(self):
        e = list(filter(lambda i: i != "", (self.full_name(), self.email, self.phone)))
        if e:
            return text_type(e[0])
        return "(id=%d)" % self.id


def _validate_provision_function(fn):
    if fn is None:
        return

    from .provision import Provision
    try:
        Provision.run_function(fn, Item.objects.none())
    except Exception as e:
        raise ValidationError(e)


class Event(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=250)
    home_page = models.URLField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()

    registration_end = models.DateTimeField(null=True, blank=True)
    checkout_active = models.BooleanField(default=False)
    mobile_view_visible = models.BooleanField(default=False)
    multiple_vendors_per_user = models.BooleanField(default=False)
    use_boxes = models.BooleanField(default=True)
    provision_function = models.TextField(
        blank=True,
        null=True,
        help_text=_("Python function body that gets sold_and_compensated queryset as"
                    " argument and must call result() with None or Decimal argument."),
        validators=[
            _validate_provision_function,
        ],
    )
    max_brought_items = models.IntegerField(
        blank=True,
        null=True,
        help_text=_("Amount of unsold Items a Vendor can have in the Event. If blank, no limit is imposed."),
        validators=[MinValueValidator(1)],
    )

    VISIBILITY_VISIBLE = 0
    VISIBILITY_NOT_LISTED = 1
    VISIBILITY = (
        (VISIBILITY_VISIBLE, _("Visible")),
        (VISIBILITY_NOT_LISTED, _("Not listed in front page")),
    )
    visibility = models.SmallIntegerField(choices=VISIBILITY, default=VISIBILITY_VISIBLE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("kirppu:vendor_view", kwargs={"event_slug": self.slug})


@python_2_unicode_compatible
class Clerk(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    access_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name=_(u"Access key value"),
        help_text=_(u"Access code assigned to the clerk. 14 hexlets."),
        validators=[RegexValidator("^[0-9a-fA-F]{14}$", message="Must be 14 hex chars.")]
    )

    class Meta:
        constraints = (
            # user may be null if access_key is set in case of "unbound Clerk object".
            # access_key may be null if the clerk object has been disabled for user.
            models.constraints.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(access_key__isnull=False),
                name="required_values",
            ),
            models.constraints.UniqueConstraint(
                fields=["access_key"],
                name="unique_access_key",
            ),
            # Only one Clerk per Event.
            models.constraints.UniqueConstraint(
                fields=["event", "user"],
                name="unique_event_clerk"
            ),
        )
        permissions = (
            ("oversee", "Can perform overseer actions"),
        )

    def __str__(self):
        if self.user is not None:
            return text_type(self.user)
        else:
            return self.access_code

    def __repr__(self):
        if self.user is not None:
            return "<Clerk: %s>" % text_type(self.user)
        else:
            return "<Clerk id=%s, code=%s...>" % (self.id, self.access_code[:5])

    def as_dict(self):
        return {
            "user": text_type(self.user),
            "print": UserAdapter.print_name(self.user),
        }

    def get_code(self):
        """
        Get access card code for this Clerk.

        Format of the code:
            zeros:       4 bits
            access_key: 56 bits
            checksum:    4 bits
            -------------------
            total:      64 bits

        :return: Clerk code.
        :rtype: str
        """
        if self.access_key in ("", None):
            return ""
        access_key = hex_to_number(self.access_key)
        return b32_encode(
            pack([
                (4, 0),
                (56, access_key),
            ], checksum_bits=4),
            length=8
        )

    @property
    def access_code(self):
        if self.access_key is not None:
            return self.get_code()
        return ""

    @property
    def access_code_str(self):
        if self.is_valid_code:
            return self.get_code()
        return "----------------"

    @classmethod
    def by_code(cls, code, **query):
        """
        Return the Clerk instance with the given hex code.

        :param code: Raw code string from access card.
        :type code: str
        :return: The corresponding Clerk or None if access token is invalid.
        :rtype: Clerk | None
        :raises: ValueError if not a valid Clerk access code.
        """
        try:
            zeros, access_key = unpack(
                b32_decode(code, length=8),
                [4, 56],
                checksum_bits=4,
            )
        except TypeError:
            raise ValueError("Not a Clerk code")

        if zeros != 0:
            raise ValueError("Not a Clerk code")

        if access_key < 100000:
            # "Valid" key, but disabled.
            raise ValueError("Clerk disabled")
        access_key_hex = number_to_hex(access_key, 56)
        try:
            clerk = cls.objects.get(access_key=access_key_hex, **query)
        except cls.DoesNotExist:
            return None
        if clerk.user is None:
            return None
        return clerk

    @property
    def is_valid_code(self):
        return self.access_key is not None and int(self.access_key, 16) >= 100000

    @property
    @short_description(_("Is enabled?"))
    def is_enabled(self):
        return self.is_valid_code and self.user is not None

    def generate_access_key(self, disabled=False):
        """
        Generate new access token for this Clerk. This will automatically overwrite old value.

        :return: The newly generated token.
        """
        if disabled:
            self.access_key = None
            return None
        key = None
        i_min = 100000
        i_max = 2 ** 56 - 1
        while key is None or Clerk.objects.filter(access_key=key).exists():
            key = random.randint(i_min, i_max)
            key = number_to_hex(key, 56)
        self.access_key = key
        return key

    def save(self, *args, **kwargs):
        # Ensure a value on access_key.
        if self.access_key is None and self.user is None:
            self.generate_access_key()
        super(Clerk, self).save(*args, **kwargs)

    @classmethod
    def generate_empty_clerks(cls, count=1, commit=True):
        """
        Generate unbound Clerks, i.e. Clerks that have access-code but no user.
        These Clerks can be "moved" to existing clerks so that the real Clerk will start
        using the access key from unbound one.

        This allows access codes to be pre-populated and printed to cards, which then can be
        taken easily to use in case of need without needing to create the card then.

        :param count: Count of unbound Clerks to generate, default 1.
        :type count: int
        :param commit: If `True` the item(s) are saved instead of just returned in the list.
        :type commit: bool
        :return: List of generated rows.
        :rtype: list[Clerk]
        """
        ids = []
        for _ in range(count):
            item = cls()
            item.generate_access_key()
            if commit:
                item.save()
            ids.append(item)
        return ids


@python_2_unicode_compatible
class Vendor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, null=True, on_delete=models.CASCADE)
    terms_accepted = models.DateTimeField(null=True)
    mobile_view_visited = models.BooleanField(default=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ("user", "person", "event"),
        )
        permissions = (
            ("can_switch_sub_vendor", "Can switch to created sub-Vendors"),
            ("can_create_sub_vendor", "Can create new sub-Vendors"),
        )

    def __repr__(self):
        return u'<Vendor: {0}>'.format(text_type(self.user) +
                                       ((" / " + text_type(self.person)) if self.person is not None else ""))

    def __str__(self):
        return text_type(self.user) if self.person is None else text_type(self.person)

    @classmethod
    def get_vendor(cls, request, event):
        """
        Get the Vendor for the given user.

        :param request: Request object, or object with `session` (dict with user_id-key and value)
         and `user` (User instance) attributes.
        :return: A Vendor, or None.
        :rtype: Vendor|None
        """
        if event.multiple_vendors_per_user and "vendor_id" in request.session:
            match = {"id": request.session["vendor_id"]}
        else:
            match = {"user": request.user, "person__isnull": True}
        try:
            return cls.objects.get(event=event, **match)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_or_create_vendor(cls, request, event):
        """
        If `create` is truthy and a vendor does not exist, one is implicitly created.

        :return:
        """
        if event.multiple_vendors_per_user and "vendor_id" in request.session:
            match = {"id": request.session["vendor_id"]}
            multi = True
        else:
            match = {"user": request.user, "person__isnull": True}
            multi = False

        try:
            return cls.objects.get(event=event, **match)
        except cls.DoesNotExist:
            if multi:
                raise ValueError("Cannot automatically create user in multi-vendor environment")
            return cls.objects.create(event=event, user=request.user)

    @classmethod
    def has_accepted(cls, request, event):
        vendor = cls.get_vendor(request, event)
        if not vendor:
            return False
        return vendor.terms_accepted is not None

    _base_dict = model_dict_fn(
        'id',
        terms_accepted=lambda self: format_datetime(self.terms_accepted) if self.terms_accepted is not None else None,
    )
    _dict_by_user = model_dict_fn(
        username=lambda self: self.user.username,
        name=lambda self: "%s %s" % (self.user.first_name, self.user.last_name),
        email=lambda self: self.user.email,
        phone=lambda self: UserAdapter.phone(self.user),
        __extend=_base_dict
    )
    _dict_by_person = model_dict_fn(
        owner=lambda self: self.user.username,
        name=lambda self: self.person.full_name(),
        email=lambda self: self.person.email,
        phone=lambda self: self.person.phone,
        __extend=_base_dict
    )

    def as_dict(self):
        if self.person is not None:
            return self._dict_by_person()
        return self._dict_by_user()


def validate_positive(value):
    if value < 0.0:
        raise ValidationError(_(u"Value cannot be negative"))


@python_2_unicode_compatible
class Box(models.Model):

    description = models.CharField(max_length=256)
    representative_item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="+")
    box_number = models.IntegerField(blank=True, null=True, db_index=True)
    bundle_size = models.IntegerField(default=1, help_text="How many items are sold in a bundle")

    def __str__(self):
        return u"{id} ({description})".format(id=self.id, description=self.description)

    as_public_dict = model_dict_fn(
        "description",
        "bundle_size",
        box_id="pk",
        item_price=lambda self: text_type(self.get_price_fmt()),
        item_count=lambda self: self.get_item_count(),
        item_type=lambda self: self.get_item_type_for_display(),
        item_adult=lambda self: self.get_item_adult(),
    )

    as_dict = model_dict_fn(
        "box_number",
        item_price=lambda self: self._get_representative_item().price_cents,
        __extend=as_public_dict
    )

    @property
    def code(self):
        return self.representative_item.code

    def get_vendor(self):
        """
        Gets the vendor of the box

        :return: Vendor object
        :rtype: Vendor
        """
        first_item = self._get_representative_item()
        return first_item.vendor

    def get_vendor_id(self):
        """
        Gets the vendor id of the box

        :return: Vendor
        :rtype: Decimal
        """
        first_item = self._get_representative_item()
        return first_item.vendor.id

    def get_items(self):
        """
        Gets items in the box.

        :return: List of Item of objects
        :rtype: Array
        """
        items = Item.objects.filter(box=self.id)
        return items

    def get_representative_item(self):
        return self._get_representative_item()

    @short_description(_("Price"))
    def get_price(self):
        return self._get_representative_item().price

    def get_price_fmt(self):
        """
        Gets the price of the items in the box

        :return: Price
        :rtype: Decimal
        """
        first_item = self._get_representative_item()
        return first_item.price_fmt

    @short_description(_("Item count"))
    def get_item_count(self):
        """
        Gets the number of items in the box.

        :return: Number of items in the box.
        :rtype: Decimal
        """
        item_count = Item.objects.filter(box=self.id).exclude(hidden=True).count()
        return item_count

    def get_item_type(self):
        """
        Gets the type of the items in the box.

        :return: Number of items in the box.
        :rtype: Decimal
        """
        first_item = self._get_representative_item()
        return first_item.itemtype

    @short_description(_("Item type"))
    def get_item_type_for_display(self):
        """
        Gets the type of the items in the box for display purpose

        :return: Number of items in the box.
        :rtype: Decimal
        """
        first_item = self._get_representative_item()
        return first_item.get_itemtype_display()

    def get_item_adult(self):
        """
        Gets the adult status of the items in the box

        :return: Number of items in the box.
        :rtype: Decimal
        """
        first_item = self._get_representative_item()
        return first_item.adult

    @short_description(_("Adult material"))
    def get_item_adult_for_display(self):
        return self._get_representative_item().get_adult_display()

    def is_hidden(self):
        """
        Checks if this box is hidden.

        The box is hidden if all the items within the box are hidden.

        :return: True if the box is hidden
        :rtype: bool
        """
        return self._get_representative_item().hidden

    def set_hidden(self, value):
        Item.objects.filter(box=self).update(hidden=value)

    def is_printed(self):
        """
        Checks if this box is printed.

        The box is printed if all the items within the box are printed.

        :return: True if the box is printed
        :rtype: bool
        """
        return self._get_representative_item().printed

    def set_printed(self, value):
        Item.objects.filter(box=self).update(printed=value)

    def _get_representative_item(self):
        return self.representative_item

    def assign_box_number(self):
        if self.box_number is None:
            with transaction.atomic():
                box_state = (
                    Box.objects
                       .filter(representative_item__vendor__event=self.representative_item.vendor.event)
                       .aggregate(last_number=models.Max("box_number"))
                )
                new_number = (box_state["last_number"] or 0) + 1

                self.box_number = new_number
                self.save(update_fields=["box_number"])

    @classmethod
    def new(cls, **kwargs):
        """
        Construct new Box and Item and generate its barcode.

        :param args: Box Constructor arguments
        :param kwargs: Item Constructor arguments
        :return: New stored Box object with calculated code.
        :rtype: Box
        """
        with transaction.atomic():
            item_title = kwargs.pop("name")
            description = kwargs.pop("description")
            count = kwargs.pop("count")
            bundle_size = kwargs.pop("bundle_size")

            representative_item = Item.new(
                name=item_title,
                **kwargs
            )
            obj = cls(
                description=description,
                representative_item=representative_item,
                bundle_size=bundle_size,
            )
            obj.full_clean()
            obj.save()

            representative_item.box = obj
            representative_item.save(
                update_fields=["box"],
            )

            # Create rest of the items for the box.
            for i in range(count - 1):
                Item.new(
                    name=item_title,
                    box=obj,
                    **kwargs
                )

        return obj


@python_2_unicode_compatible
class ItemType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    key = models.CharField(max_length=24)
    order = models.IntegerField()
    title = models.CharField(max_length=255)

    class Meta:
        unique_together = (
            ("event", "key"),
            ("event", "order"),
        )

    def __str__(self):
        return self.title

    def __repr__(self):
        return u"ItemType(key={key}, order={order}, title={title})".format(
            key=repr(self.key),
            order=self.order,
            title=repr(self.title)
        )

    @classmethod
    def as_tuple(cls, event=None):
        if event is not None:
            query = cls.objects.filter(event=event)
        else:
            query = cls.objects
        return query.order_by("order").values_list("key", "title")


@python_2_unicode_compatible
class Item(models.Model):
    ADVERTISED = "AD"
    BROUGHT = "BR"
    STAGED = "ST"
    SOLD = "SO"
    MISSING = "MI"
    RETURNED = "RE"
    COMPENSATED = "CO"

    STATE = (
        (ADVERTISED, _(u"Advertised")),
        (BROUGHT, _(u"Brought to event")),
        (STAGED, _(u"Staged for selling")),
        (SOLD, _(u"Sold")),
        (MISSING, _(u"Missing")),
        (RETURNED, _(u"Returned to vendor")),
        (COMPENSATED, _(u"Compensated to vendor")),
    )

    TYPE_TINY = "tiny"
    TYPE_SHORT = "short"
    TYPE_LONG = "long"
    TYPE = (
        (TYPE_TINY, _(u"Tiny price tag")),
        (TYPE_SHORT, _(u"Short price tag")),
        (TYPE_LONG, _(u"Long price tag")),
    )

    ADULT_YES = "yes"
    ADULT_NO = "no"
    ADULT = (
        (ADULT_YES, _(u"Item allowed only to adult shoppers, contains porn etc.")),
        (ADULT_NO, _(u"Item allowed to all shoppers")),
    )

    # Count of digits after decimal separator.
    FRACTION_LEN = 2

    # Denominator, a power of 10, for representing numbers with FRACTION_LEN digits.
    FRACTION = 10 ** FRACTION_LEN

    # Number "one", represented with precision defined by FRACTION(_LEN).
    Q_EXP = Decimal(FRACTION).scaleb(-FRACTION_LEN)

    CODE_BITS = 40

    code = models.CharField(
        max_length=16,
        blank=True,
        null=False,
        db_index=True,
        unique=True,
        help_text=_(u"Barcode content of the product"),
    )
    name = models.CharField(max_length=256, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[validate_positive])
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    state = models.CharField(
        choices=STATE,
        max_length=8,
        default=ADVERTISED
    )
    type = models.CharField(
        choices=TYPE,
        max_length=8,
        default=TYPE_SHORT
    )
    itemtype = models.ForeignKey(ItemType, on_delete=models.CASCADE)
    adult = models.CharField(
        choices=ADULT,
        max_length=8,
        default=ADULT_NO
    )
    abandoned = models.BooleanField(default=False)

    # Has the user marked this item as printed?
    # Affects whether the item is shown in print view or not.
    printed = models.BooleanField(default=False)

    # Affects whether the item is shown at all.
    hidden = models.BooleanField(default=False)
    box = models.ForeignKey(Box, on_delete=models.CASCADE, blank=True, null=True)

    lost_property = models.BooleanField(
        default=False,
        help_text=_(u"Forgotten or lost property/item"),
    )

    class Meta:
        permissions = (
            ("register_override", _("Can register items after registration is closed")),
        )

    def __str__(self):
        return u"{name} ({code})".format(name=self.name, code=self.code)

    as_dict = model_dict_fn(
        "code",
        "name",
        "state",
        "abandoned",
        "hidden",
        price="price_cents",
        vendor="vendor_id",
        state_display="get_state_display",
        itemtype=lambda self: self.itemtype.key,
        itemtype_display="get_itemtype_display",
        adult=lambda self: self.adult == Item.ADULT_YES,
    )

    as_public_dict = model_dict_fn(
        "vendor_id",
        "code",
        "name",
        "type",
        "adult",
        price=lambda self: str(self.price).replace(".", ","),
    )

    def get_itemtype_display(self):
        return self.itemtype.title

    @property
    def price_cents(self):
        return decimal_to_transport(self.price)

    @property
    def price_fmt(self):
        """
        Get Item price formatted human-printable:
        If the value is exact integer, returned value contains only the integer part.
        Else, the value precision is as defined with FRACTION variable.

        :return: Decimal object formatted for humans.
        :rtype: Decimal
        """
        return self.price_fmt_for(self.price)

    @staticmethod
    def price_fmt_for(value):
        # If value is exact integer, return only the integer part.
        int_value = value.to_integral_value()
        if int_value == value:
            return int_value
        # Else, display digits with precision from FRACTION*.
        return value.quantize(Item.Q_EXP)

    @classmethod
    def new(cls, *args, **kwargs):
        """
        Construct new Item and generate its barcode.

        :param args: Item Constructor arguments
        :param kwargs: Item Constructor arguments
        :return: New stored Item object with calculated code.
        :rtype: Item
        """
        obj = cls(*args, **kwargs)
        obj.code = Item.gen_barcode()
        obj.full_clean()
        obj.save()

        ItemStateLog.objects.create(item=obj, old_state="", new_state=obj.state)

        return obj

    @classmethod
    def gen_barcode(cls):
        """
        Generate new random barcode for item.

        Format of the code:
            random:     36 bits
            checksum:    4 bits
            -------------------
            total:      40 bits


        :return: The newly generated code.
        :rtype: str
        """
        checksum_bits = 4
        data_bits = cls.CODE_BITS - checksum_bits
        key = None
        i_max = 2 ** data_bits - 1
        while key is None or Item.objects.filter(code=key).exists():
            key = b32_encode(
                pack([
                    (data_bits, random.randint(1, i_max)),
                ], checksum_bits=checksum_bits)
            )
        return key

    def is_locked(self):
        return self.state != Item.ADVERTISED

    @staticmethod
    def get_item_by_barcode(data, **kwargs):
        """
        Get Item by barcode.

        :param data: Barcode data scanned from product
        :type data: str

        :rtype: Item
        :raise Item.DoesNotExist: If no Item matches the code.
        """
        return Item.objects.annotate(vendor_event=F("vendor__event__id")).get(code=data, **kwargs)

    @staticmethod
    def get_item_by_barcode_for_update(data, **kwargs):
        return Item.objects.annotate(vendor_event=F("vendor__event__id")).select_for_update().get(code=data, **kwargs)

    @classmethod
    def is_item_barcode(cls, text):
        """
        Do a simple test whether given string could be a Item barcode.

        :param text: String to test.
        :type text: str
        :return: True if the string could be a (full) barcode. False if not.
        :rtype: bool
        """
        return text.isalnum() and text.isupper() and len(text) == cls.CODE_BITS / 5


@python_2_unicode_compatible
class UIText(models.Model):
    def __str__(self):
        return self.identifier

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    identifier = models.CharField(
        max_length=16,
        help_text=_(u"Identifier of the textitem")
    )
    text = models.CharField(
        blank=True,
        max_length=16384,
        help_text=_(u"Textitem in UI")
    )

    class Meta:
        unique_together = (("event", "identifier"),)

    @property
    def text_excerpt(self):
        return shorten_text(self.text)

    @classmethod
    def get_text(cls, event, identifier, default=None):
        try:
            return UIText.objects.values_list("text", flat=True).get(event=event, identifier=identifier)
        except UIText.DoesNotExist:
            return default


@python_2_unicode_compatible
class Counter(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    identifier = models.CharField(
        max_length=32,
        blank=True,
        null=False,
        help_text=_(u"Registration identifier of the counter")
    )
    name = models.CharField(
        max_length=64,
        blank=True,
        null=False,
        help_text=_(u"Common name of the counter")
    )

    class Meta:
        unique_together = (
            ("event", "identifier"),
        )

    def __str__(self):
        return u"{1} ({0})".format(self.identifier, self.name)


@python_2_unicode_compatible
class ReceiptItem(models.Model):
    ADD = "ADD"
    REMOVED_LATER = "RL"
    REMOVE = "DEL"

    ACTION = (
        (ADD, _(u"Added to receipt")),
        (REMOVED_LATER, _(u"Removed later")),
        (REMOVE, _(u"Removed from receipt")),
    )

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    receipt = models.ForeignKey("Receipt", on_delete=models.CASCADE)
    action = models.CharField(choices=ACTION, max_length=16, default=ADD)
    add_time = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        ret = {
            "action": self.action,
        }
        ret.update(self.item.as_dict())
        return ret

    def __str__(self):
        return text_type(self.item)


@python_2_unicode_compatible
class Receipt(models.Model):
    PENDING = "PEND"
    FINISHED = "FINI"
    SUSPENDED = "SUSP"
    ABORTED = "ABRT"

    STATUS = (
        (PENDING, _(u"Not finished")),
        (FINISHED, _(u"Finished")),
        (SUSPENDED, _(u"Suspended")),
        (ABORTED, _(u"Aborted")),
    )

    TYPE_PURCHASE = "PURCHASE"
    TYPE_COMPENSATION = "COMPENSATION"

    TYPES = (
        (TYPE_PURCHASE, _(u"Purchase")),
        (TYPE_COMPENSATION, _(u"Compensation")),
    )

    items = models.ManyToManyField(Item, through=ReceiptItem)
    status = models.CharField(choices=STATUS, max_length=16, default=PENDING)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    clerk = models.ForeignKey(Clerk, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    type = models.CharField(choices=TYPES, max_length=16, default=TYPE_PURCHASE)

    def items_list(self):
        return [
            row.as_dict()
            for row in self.receiptitem_set.select_related("item", "item__itemtype").order_by("add_time")
        ]

    def row_list(self):
        r = self.items_list()
        r.extend([row.as_dict() for row in self.extra_rows.all()])
        return r

    @property
    def total_cents(self):
        return decimal_to_transport(self.total)

    as_dict = model_dict_fn(
        "status",
        "type",
        id="pk",
        total="total_cents",
        status_display=lambda self: self.get_status_display(),
        start_time=lambda self: format_datetime(self.start_time),
        end_time=lambda self: format_datetime(self.end_time) if self.end_time is not None else None,
        clerk=lambda self: self.clerk.as_dict(),
        counter=lambda self: self.counter.name,
        notes=lambda self: [note.as_dict() for note in self.receiptnote_set.order_by("timestamp")],
        type_display=lambda self: self.get_type_display(),
    )

    def calculate_total(self):
        result = ReceiptItem.objects.filter(action=ReceiptItem.ADD, receipt=self)\
            .aggregate(price_total=Sum("item__price"))
        extras = ReceiptExtraRow.objects.filter(receipt=self).aggregate(extras_total=Sum("value"))

        price_total = result["price_total"]
        extras_total = extras["extras_total"]

        self.total = (price_total or 0) + (extras_total or 0)
        return self.total

    def __str__(self):
        return "{type}: {start} / {clerk}".format(
            type=self.get_type_display(),
            start=text_type(self.start_time),
            clerk=text_type(self.clerk),
        )

    class Meta:
        permissions = (
            ("view_accounting", "View accounting data"),
        )


@python_2_unicode_compatible
class ReceiptExtraRow(models.Model):
    TYPE_PROVISION = "PRO"
    TYPE_PROVISION_FIX = "PRO_FIX"
    TYPES = (
        (TYPE_PROVISION, _("Provision")),
        (TYPE_PROVISION_FIX, _("Provision balancing")),
    )

    type = models.CharField(max_length=8, choices=TYPES)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name="extra_rows")

    as_dict = model_dict_fn(
        "type",
        type_display=lambda self: self.get_type_display(),
        action=lambda _: "EXTRA",  # Same key as in ReceiptItem.action.
        value="value_cents",
    )

    @property
    def value_cents(self):
        return decimal_to_transport(self.value)

    def __str__(self):
        return "{}: {} ({})".format(self.get_type_display(), self.value, self.receipt)


@python_2_unicode_compatible
class ReceiptNote(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    clerk = models.ForeignKey(Clerk, on_delete=models.CASCADE)
    text = models.TextField()
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE)

    as_dict = model_dict_fn(
        "text",
        timestamp=lambda self: format_datetime(self.timestamp),
        clerk=lambda self: self.clerk.as_dict(),
    )

    def __str__(self):
        return text_type(self.timestamp) + u" / " + text_type(self.clerk) + u" @ " + text_type(self.receipt_id)


class ItemStateLogManager(models.Manager):
    @staticmethod
    def _make_log_state(request, doit):
        from .ajax_util import get_clerk, get_counter, AjaxError
        counter = None
        clerk = None
        try:
            clerk = get_clerk(request)
            counter = get_counter(request)
        except AjaxError:
            if request.user.is_authenticated:
                try:
                    clerk = Clerk.objects.get(user=request.user)
                except Clerk.DoesNotExist:
                    clerk = None

        return doit(counter, clerk)

    def log_state(self, item, new_state, request):
        def actual(counter, clerk):
            return self.create(
                item=item,
                old_state=item.state,
                new_state=new_state,
                clerk=clerk,
                counter=counter)
        return self._make_log_state(request, actual)

    def log_states(self, item_set, new_state, request):
        def actual(counter, clerk):
            objs = [
                ItemStateLog(
                    item=item,
                    old_state=item.state,
                    new_state=new_state,
                    clerk=clerk,
                    counter=counter
                )
                for item in item_set
            ]
            return self.bulk_create(objs)
        return self._make_log_state(request, actual)


class ItemStateLog(models.Model):
    objects = ItemStateLogManager()

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    old_state = models.CharField(
        choices=Item.STATE,
        max_length=2,
    )
    new_state = models.CharField(
        choices=Item.STATE,
        max_length=2,
    )

    clerk = models.ForeignKey(Clerk, null=True, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, null=True, on_delete=models.CASCADE)

    def __repr__(self):
        return "<ItemStateLog item={} time={} old={} new={} clerk={} counter={}>".format(
            self.item.code,
            self.time,
            self.old_state,
            self.new_state,
            self.clerk.pk if self.clerk is not None else "",
            self.counter.pk if self.counter is not None else "",
        )

    class Meta:
        permissions = (
            ("view_statistics", "Can see statistics"),
        )


def default_temporary_access_permit_expiry():
    return timezone.now() + timezone.timedelta(minutes=settings.KIRPPU_SHORT_CODE_EXPIRATION_TIME_MINUTES)


@python_2_unicode_compatible
class TemporaryAccessPermit(models.Model):
    STATE_UNUSED = "new"
    STATE_IN_USE = "use"
    STATE_EXHAUSTED = "exh"
    STATE_INVALIDATED = "inv"
    STATES = (
        (STATE_UNUSED, _("Unused")),
        (STATE_IN_USE, _("In use")),
        (STATE_EXHAUSTED, _("Exhausted")),
        (STATE_INVALIDATED, _("Invalidated")),
    )

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, db_index=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    expiration_time = models.DateTimeField(default=default_temporary_access_permit_expiry)
    state = models.CharField(choices=STATES, default=STATE_UNUSED, max_length=8)
    creator = models.ForeignKey(Clerk, on_delete=models.DO_NOTHING)
    short_code = models.CharField(max_length=128, unique=True, validators=[MinLengthValidator(4)])

    def __str__(self):
        return "{vendor} ({state} / {expiry})".format(
            vendor=UserAdapter.print_name(self.vendor.user),
            state=self.get_state_display(),
            expiry=self.expiration_time,
        )


@python_2_unicode_compatible
class TemporaryAccessPermitLog(models.Model):
    ACTION_ADD = "add"
    ACTION_TRY = "try"
    ACTION_USE = "use"
    ACTION_DELETE = "del"
    ACTION_INVALIDATE = "inv"
    ACTIONS = (
        (ACTION_ADD, _("Add")),
        (ACTION_TRY, _("Try using")),
        (ACTION_USE, _("Use")),
        (ACTION_DELETE, _("Delete")),
        (ACTION_INVALIDATE, _("Invalidate")),
    )

    permit = models.ForeignKey(TemporaryAccessPermit, on_delete=models.DO_NOTHING, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=16, choices=ACTIONS)
    address = models.CharField(max_length=512)
    peer = models.CharField(max_length=1024)

    def __str__(self):
        return "{action} ({code}) / {vendor} / {timestamp}".format(
            action=self.get_action_display(),
            code=self.permit.short_code,
            vendor=self.permit.vendor,
            timestamp=self.timestamp,
        )
