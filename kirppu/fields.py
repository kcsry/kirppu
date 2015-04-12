from django.forms.fields import Field
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

import decimal
from decimal import Decimal, InvalidOperation

class ItemPriceField(Field):

    default_error_messages = {
        'invalid': _('Price must be numeric.'),
        'required': _('Item must have a price.'),
        'min_value': _(u"Price too low. (min 0.5 euros)"),
        'max_value': _(u"Price too high. (max 400 euros)"),
    }

    def __init__(self, **kwargs):
        super(ItemPriceField, self).__init__(**kwargs)

    def to_python(self, value):
        value = super(ItemPriceField, self).to_python(value)
        if value in self.empty_values:
            return None

        value = value.replace(",", ".")
        try:
            value = Decimal(value).quantize(Decimal('0.1'), rounding=decimal.ROUND_UP)
        except InvalidOperation:
            raise ValidationError(self.error_messages['invalid'], code='invalid')

        # Round up to nearest 50 cents.
        remainder = value % Decimal('.5')
        if remainder > Decimal('0'):
            value += Decimal('.5') - remainder

        return value

    def validate(self, value):
        super(ItemPriceField, self).validate(value)
        if value <= Decimal('0'):
            raise ValidationError(self.error_messages['min_value'], code='min_value')
        if value > Decimal('400'):
            raise ValidationError(self.error_messages['max_value'], code='max_value')
