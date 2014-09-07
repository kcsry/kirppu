class @ItemReceiptTable extends ResultTable
  constructor: ->
    super
    @head.append([
      '<th class="receipt_index">#</th>'
      '<th class="receipt_code">' + gettext('code') + '</th>'
      '<th class="receipt_item">' + gettext('item') + '</th>'
      '<th class="receipt_price">' + gettext('price') + '</th>'
    ].map($))
