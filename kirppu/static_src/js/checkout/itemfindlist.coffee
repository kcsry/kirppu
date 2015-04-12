class @ItemFindList extends ResultTable
  constructor: ->
    super
    @head.append([
      '<th class="receipt_index">#</th>'
      '<th class="receipt_code">' + gettext('code') + '</th>'
      '<th class="receipt_item">' + gettext('item') + '</th>'
      '<th class="receipt_price">' + gettext('price') + '</th>'
      '<th class="receipt_type">' + gettext('type') + '</th>'
      '<th class="receipt_name">' + gettext('vendor') + '</th>'
      '<th class="receipt_status">' + gettext('status') + '</th>'
    ].map($))

  append: (item, index, action) ->
    row = $("<tr>")
      .addClass('receipt_tr_clickable')
      .click(-> action(item))
    row.append([
      $('<td class="receipt_index numeric">').text(index)
      $('<td class="receipt_code">').text(item.code)
      $('<td class="receipt_item">').text(item.name)
      $('<td class="receipt_price numeric">').text(displayPrice(item.price))
      $('<td class="receipt_type">').text(item.itemtype_display)
      $('<td class="receipt_name">').text(item.vendor.name)
      $('<td class="receipt_status">').text(item.state_display)
    ])
    @body.append(row)
