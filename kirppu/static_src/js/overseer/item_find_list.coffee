class @ItemFindList extends ResultTable
  @vendorField = "%n (%i)"
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
    if item.hidden
      row.addClass("text-muted")
    vendor = dPrintF(@constructor.vendorField,
      n: item.vendor.name
      i: item.vendor.id
    )
    name_field = $('<td class="receipt_item">').text(item.name)
    if item.box?
      box_number = item.box.box_number ? "??"
      name_field.append(" ")
      name_field.append($('<span class="label label-info">').text(
        "#" + box_number + ", n=" + item.box.item_count)
      )
    if item.box? and item.box.bundle_size > 1
      price_field = $('<td class="receipt_price numeric">').text(displayPrice(item.price) + " / " + item.box.bundle_size)
    else
      price_field = $('<td class="receipt_price numeric">').text(displayPrice(item.price))

    row.append([
      $('<td class="receipt_index numeric">').text(index)
      $('<td class="receipt_code">').text(item.code)
      name_field
      price_field
      $('<td class="receipt_type">').text(item.itemtype_display)
      $('<td class="receipt_name">').text(vendor)
      $('<td class="receipt_status">').text(item.state_display)
    ])
    @body.append(row)

  no_results: () ->
    row = $("<tr>")
    row.append([
      $('<td colspan="2">')
      $('<td colspan="5">').text(gettext("No results."))
    ])
    @body.append(row)
