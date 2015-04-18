import re
from django import forms
from django.core import validators
from django.contrib.auth import get_user_model

from .models import (
    Clerk,
    ReceiptItem,
    Receipt,
    Item,
    UIText,
    Vendor,
)
from .utils import StaticText, ButtonWidget


class ClerkGenerationForm(forms.ModelForm):
    count = forms.IntegerField(
        min_value=0,
        initial=1,
        help_text=u"Count of empty Clerks to generate")

    def __init__(self, *args, **kwargs):
        super(ClerkGenerationForm, self).__init__(*args, **kwargs)
        self._save_list = None
        self._saved_list = None

    def generate(self, commit=True):
        return Clerk.generate_empty_clerks(self.cleaned_data["count"], commit=commit)

    def save(self, commit=True):
        # Save-hack... Admin calls this first with commit=False and then commit=True,
        # so store the list of items at first time to variable, and do the real saving
        # when the commit is True.
        if self._save_list is not None:
            if commit:
                for item in self._save_list:
                    item.save()
                self._saved_list = self._save_list
                self._save_list = None
            return self

        if commit:
            # Called directly commit=True, so do so.
            self._saved_list = self.generate(commit=True)
            return self

        else:
            self._save_list = self.generate(commit=False)
            # Admin expects to find verbose_name from Meta, which does not exist in
            # ModelFormOptions, so add kind of own name there.
            if "verbose_name" not in dir(self._meta):
                self._meta.verbose_name = "ClerkGeneration"
            return self

    # noinspection PyMethodMayBeStatic
    def _get_pk_val(self):
        # (Save-hack)
        return 0

    def __unicode__(self):
        # (Save-hack) When form is valid, this is used in the "Created x" -message.
        if self.is_valid():
            return u"{0} of Clerk(s)".format(self.cleaned_data["count"])

        return "ClerkGenerationForm"

    @property
    def saved_list(self):
        return self._saved_list

    class Meta:
        model = Clerk
        fields = ("count",)


class ClerkSSOForm(forms.ModelForm):
    user = forms.CharField(
        max_length=30,
        validators=[
            validators.RegexValidator(
                re.compile('^[\w.@+-]+$'),
                'Enter a valid username.',
                'invalid'
            )
        ]
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

        from kompassi_crowd.kompassi_client import user_defaults_from_kompassi as user_defaults
        user, created = get_user_model().objects.get_or_create(
            username=username,
            defaults=user_defaults(self._sso_user)
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
        help_text=u"Clerk will be disabled or enabled on save.",
    )
    regen_code = forms.BooleanField(
        required=False,
        help_text=u"Enabled Clerk access code will be regenerated on save."
    )

    def __init__(self, *args, **kwargs):
        instance = kwargs["instance"]
        """:type: Clerk"""

        self._access_key = instance.access_key
        self._disabled = not instance.is_enabled
        if instance.user is not None:
            user = u"{0} (id={1})".format(unicode(instance.user.username), instance.user.id)
        else:
            user = u"<Unbound>"

        kwargs["initial"] = dict(
            user=user,
            access_key=u"{0} (raw={1})".format(instance.access_code, instance.access_key).strip(),
            disabled=self._disabled,
        )
        super(ClerkEditForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        # Save only if disabled has changed.

        disabled = self.cleaned_data["disabled"]
        if disabled and self._disabled == disabled and self.instance.access_key is not None:
            return self.instance
        elif self._disabled == disabled and not self.cleaned_data["regen_code"]:
            return self.instance

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
    # noinspection PyProtectedMember
    text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"cols": 100}),
        help_text=UIText._meta.get_field("text", False).help_text
    )

    class Meta:
        model = UIText
        fields = ("identifier", "text")


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
    start_time = StaticText(
        label=u"Start time",
        text=u"--"
    )

    def __init__(self, *args, **kwargs):
        super(ReceiptAdminForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            mdl = kwargs["instance"]
            self.fields["start_time"].widget.set_text(mdl.start_time)


class ItemRemoveForm(forms.Form):
    receipt = forms.IntegerField(min_value=0, label=u"Receipt ID")
    item = forms.CharField(label=u"Item code")

    def __init__(self, *args, **kwargs):
        super(ItemRemoveForm, self).__init__(*args, **kwargs)
        self.last_added_item = None
        self.item = None
        self.receipt = None

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
        receipt = Receipt.objects.get(pk=receipt_id)

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

    def save(self):
        assert self.last_added_item is not None

        last_added_item = self.last_added_item[0]
        last_added_item.action = ReceiptItem.REMOVED_LATER
        last_added_item.save()

        removal_entry = ReceiptItem(item=self.item, receipt=self.receipt, action=ReceiptItem.REMOVE)
        removal_entry.save()

        self.receipt.calculate_total()
        self.receipt.save()

        self.item.state = Item.BROUGHT
        self.item.save()


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

        from django.core.urlresolvers import reverse
        url = reverse("kirppuauth:local_admin_login")
        click = u"""document.forms[0].action='{0}'; document.forms[0].submit();""".format(url)
        self.fields["set_user"].widget.set_click(click)

    class Meta:
        model = Vendor
        fields = ()
