class @LostAndFoundTable extends ResultTable
  constructor: ->
    super
    @head.append([
      '<th class="receipt_code">' + gettext('code') + '</th>'
      '<th class="receipt_item">' + gettext('item') + '</th>'
      '<th class="receipt_item_state">' + gettext('state') + '</th>'
      '<th class="receipt_vendor_id">' + gettext('vendor') + '</th>'
    ].map($))

  append: (item) ->
    row = $('<tr>')

    row.append([
      $('<td>').text(item.code)
      $('<td>').text(item.name)
      $('<td>').text(item.state_display)
      $('<td>').text(item.vendor)
    ])

    @body.append(row)
