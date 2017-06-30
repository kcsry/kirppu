from __future__ import unicode_literals, print_function, absolute_import
import re
from django import forms
from django.core import validators
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy as _

from .fields import ItemPriceField, SuffixField, StripField
from .models import (
    Clerk,
    ReceiptItem,
    Receipt,
    Item,
    UIText,
    Vendor,
    ItemStateLog,
)
from .util import shorten_text
from .utils import StaticText, ButtonWidget, model_dict_fn


class ClerkGenerationForm(forms.Form):
    count = forms.IntegerField(
        min_value=0,
        initial=1,
        help_text=u"Count of empty Clerks to generate")

    def __init__(self, *args, **kwargs):
        super(ClerkGenerationForm, self).__init__(*args, **kwargs)

    def get_fieldsets(self):
        return [(None, {'fields': self.base_fields})]

    def generate(self, commit=True):
        return Clerk.generate_empty_clerks(self.get_count(), commit=commit)

    def get_count(self):
        return self.cleaned_data["count"]


class ClerkSSOForm(forms.ModelForm):
    user = forms.CharField(
        max_length=30,
        validators=[
            validators.RegexValidator(
                re.compile('^[\w.@+-]+$'),
                'Enter a valid username.',
                'invalid'
            )
        ],
        label=_("Username"),
    )

    def __init__(self, *args, **kwargs):
        super(ClerkSSOForm, self).__init__(*args, **kwargs)
        self._sso_user = None

    def clean_user(self):
        username = self.cleaned_data["user"]
        user = get_user_model().objects.filter(username=username)
        if len(user) > 0:
            clerk = Clerk.objects.filter(user=user[0])
            if len(clerk) > 0:
                raise forms.ValidationError(u"Clerk already exists.")

        from kompassi_crowd.kompassi_client import KompassiError, kompassi_get
        try:
            self._sso_user = kompassi_get('people', username)
        except KompassiError as e:
            raise forms.ValidationError(u'Failed to get Kompassi user {username}: {e}'.format(
                username=username, e=e)
            )

        return username

    def save(self, commit=True):
        username = self.cleaned_data["user"]
        user = get_user_model().objects.filter(username=username)
        if len(user) > 0 and user[0].password != "":
            clerk = Clerk(user=user[0])
            if commit:
                clerk.save()
            return clerk

        from kompassi_crowd.kompassi_client import user_defaults_from_kompassi
        user, created = get_user_model().objects.get_or_create(
            username=username,
            defaults=user_defaults_from_kompassi(self._sso_user)
        )

        clerk = Clerk(user=user)
        if commit:
            clerk.save()
        return clerk

    class Meta:
        model = Clerk
        exclude = ("user", "access_key")


class ClerkEditForm(forms.ModelForm):
    """
        Edit form for Clerks in Admin-site.
        Does not allow editing user or access_key, but access_key is updated based on
        selection of disabled and regen_code fields.
    """
    user = forms.CharField(
        widget=forms.TextInput(attrs=dict(readonly="readonly", size=60)),
        help_text=u"Read only",
    )
    access_key = forms.CharField(
        widget=forms.TextInput(attrs=dict(readonly="readonly", size=60)),
        help_text=u"Read only",
    )
    disabled = forms.BooleanField(
        required=False,
        label=_("Disabled"),
        help_text=_("Clerk will be disabled or enabled on save."),
    )
    regen_code = forms.BooleanField(
        required=False,
        label=_("Regenerate access code"),
        help_text=_("Enabled Clerk access code will be randomized on save."),
    )
    change_code = forms.ModelChoiceField(
        queryset=Clerk.objects.filter(user__isnull=True),
        label=_("Change access code"),
        help_text=_("Clerk access code will be changed to this on save."),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        instance = kwargs["instance"]
        """:type: Clerk"""

        self._access_key = instance.access_key
        self._disabled = not instance.is_valid_code
        if instance.user is not None:
            user = u"{0} (id={1})".format(text_type(instance.user.username), instance.user.id)
        else:
            user = u"<Unbound>"

        kwargs["initial"] = dict(
            user=user,
            access_key=u"{0} (raw={1})".format(instance.access_code, instance.access_key).strip(),
            disabled=self._disabled,
        )
        super(ClerkEditForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ClerkEditForm, self).clean()
        is_disabled = cleaned_data["disabled"]
        is_regen_code = cleaned_data["regen_code"]
        is_change_code = cleaned_data["change_code"]
        msg = None

        labels = {
            "disabled": self.fields["disabled"].label,
            "regen": self.fields["regen_code"].label,
            "change": self.fields["change_code"].label,
        }

        if is_disabled and is_change_code:
            msg = ValidationError(_('Either "%(disabled)s" or "%(change)s" must be cleared.'),
                                  params=labels,
                                  code="set_disabled_and_change_code")
            self.add_error("disabled", msg)
            self.add_error("change_code", msg)

        if is_regen_code and is_change_code:
            msg = ValidationError(_('Either "%(regen)s" or "%(change)s" must be cleared.'),
                                  params=labels,
                                  code="regenerate_and_change_code")
            self.add_error("regen_code", msg)
            self.add_error("change_code", msg)

        if msg is not None:
            raise ValidationError(_("Only one option may be selected at a time."),
                                  code="operation_conflict")

        return cleaned_data

    def save(self, commit=True):
        # Save only if disabled has changed.

        disabled = self.cleaned_data["disabled"]
        regen = self.cleaned_data["regen_code"]
        change = self.cleaned_data["change_code"]
        if disabled and self._disabled == disabled and self.instance.access_key is not None:
            # Do nothing if setting disabled to a clerk that is disabled (but not None).
            return self.instance
        elif self._disabled == disabled and not regen and not change:
            # Do nothing if not changing disabled and there is no other operation too.
            return self.instance

        if change:
            self.instance.access_key = change.access_key
            if commit:
                change.delete()
        else:
            self.instance.generate_access_key(disabled=disabled)

        if commit:
            self.instance.save()
        return self.instance

    @property
    def changed_data(self):
        """Overridden function to create a little more descriptive log info into admin log."""

        disabled = self.cleaned_data["disabled"]
        if disabled == self._disabled:
            if self.instance.access_key == self._access_key:
                return []
            else:
                return ["access_key"]
        if disabled:
            return ["setDisabled"]
        return ["setEnabled"]

    class Meta:
        model = Clerk
        # Exclude model functionality for these fields.
        exclude = ("user", "access_key")


class UITextForm(forms.ModelForm):
    class Meta:
        model = UIText
        fields = "__all__"
        widgets = {
            "text": forms.Textarea(attrs={"cols": 100}),
        }


class ReceiptItemAdminForm(forms.ModelForm):
    price = StaticText(
        label=u"Price",
        text=u"--",
    )

    def __init__(self, *args, **kwargs):
        super(ReceiptItemAdminForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            mdl = kwargs["instance"]
            self.fields["price"].widget.set_text(mdl.item.price)

    class Meta:
        model = ReceiptItem
        fields = ("item", "receipt", "action")


class ReceiptAdminForm(forms.ModelForm):
    # Django 1.10 does not allow same name to be used when overriding read-only -properties.
    # TODO: Maybe show this as description for state?
    start_time_ = StaticText(
        label=u"Start time",
        text=u"--"
    )

    def __init__(self, *args, **kwargs):
        super(ReceiptAdminForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            mdl = kwargs["instance"]
            self.fields["start_time_"].widget.set_text(mdl.start_time)


class ItemRemoveForm(forms.Form):
    receipt = forms.IntegerField(min_value=0, label=u"Receipt ID")
    item = forms.CharField(label=u"Item code")

    def __init__(self, *args, **kwargs):
        super(ItemRemoveForm, self).__init__(*args, **kwargs)
        self.last_added_item = None
        self.item = None
        self.receipt = None
        self.removal_entry = None

    def clean_receipt(self):
        data = self.cleaned_data["receipt"]
        if not Receipt.objects.filter(pk=data).exists():
            raise forms.ValidationError(u"Receipt {pk} not found.".format(pk=data))
        return data

    def clean_item(self):
        data = self.cleaned_data["item"]
        if not Item.objects.filter(code=data).exists():
            raise forms.ValidationError(u"Item with code {code} not found.".format(code=data))
        return data

    def clean(self):
        cleaned_data = super(ItemRemoveForm, self).clean()
        if "receipt" not in cleaned_data or "item" not in cleaned_data:
            return cleaned_data
        receipt_id = cleaned_data["receipt"]
        code = cleaned_data["item"]

        item = Item.objects.get(code=code)
        receipt = Receipt.objects.get(pk=receipt_id, type=Receipt.TYPE_PURCHASE)

        last_added_item = ReceiptItem.objects\
            .filter(receipt=receipt, item=item, action=ReceiptItem.ADD)\
            .order_by("-add_time")

        if len(last_added_item) == 0:
            raise forms.ValidationError(u"Item is not added to receipt.")
        assert len(last_added_item) == 1

        self.last_added_item = last_added_item
        self.item = item
        self.receipt = receipt
        return cleaned_data

    @transaction.atomic
    def save(self, request):
        assert self.last_added_item is not None

        last_added_item = self.last_added_item[0]
        last_added_item.action = ReceiptItem.REMOVED_LATER
        last_added_item.save()

        removal_entry = ReceiptItem(item=self.item, receipt=self.receipt, action=ReceiptItem.REMOVE)
        removal_entry.save()

        self.receipt.calculate_total()
        self.receipt.save()

        if self.item.state != Item.BROUGHT:
            ItemStateLog.objects.log_state(item=self.item, new_state=Item.BROUGHT, request=request)
            self.item.state = Item.BROUGHT
            self.item.save()
        self.removal_entry = removal_entry


class VendorSetSelfForm(forms.ModelForm):

    set_user = StaticText(
        u"Set self as this user.",
        label="",
        widget=ButtonWidget,
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
    )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance", None)
        """:type: Vendor"""

        kwargs["initial"] = {
            "username": instance.user.username,
        }

        super(VendorSetSelfForm, self).__init__(*args, **kwargs)

        from django.urls import reverse
        url = reverse("kirppuauth:local_admin_login")
        click = u"""document.forms[0].action='{0}'; document.forms[0].submit();""".format(url)
        self.fields["set_user"].widget.set_click(click)

    class Meta:
        model = Vendor
        fields = ()


class VendorItemForm(forms.Form):
    name = StripField(error_messages={"required": _("Name is required.")}, max_length=256)
    price = ItemPriceField()
    tag_type = forms.ChoiceField(
        required=False,
        choices=[i for i in Item.TYPE if i != "long"],
    )
    suffixes = SuffixField()
    item_type = forms.ChoiceField(
        choices=Item.ITEMTYPE,
        error_messages={"required": _(u"Item must have a type.")}
    )
    adult = forms.BooleanField(required=False)

    def get_any_error(self):
        errors = self.errors.as_data()
        keys = errors.keys()
        if len(keys) == 0:
            return None
        some_error = errors[list(keys)[0]]
        return u" ".join([u" ".join(error.messages) for error in some_error])

    def clean_tag_type(self):
        value = self.cleaned_data["tag_type"]
        if not value:
            return Item.TYPE_SHORT
        return value

    db_values = model_dict_fn(
        "name",
        type="tag_type",
        itemtype="item_type",
        adult=lambda self: "yes" if self.cleaned_data["adult"] else "no",
        price=lambda self: str(self.cleaned_data["price"]),
        __access_fn=lambda self, value: self.cleaned_data[value],
    )


class VendorBoxForm(VendorItemForm):
    description = StripField(max_length=256)
    name = None
    count = forms.IntegerField(min_value=1)

    db_values = model_dict_fn(
        "description",
        "count",
        type=None,
        name=lambda self: shorten_text(self.cleaned_data["description"], 32),
        __extend=VendorItemForm.db_values,
        __access_fn=lambda self, value: self.cleaned_data[value],
    )
