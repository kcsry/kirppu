class @ItemReportTable extends ItemReceiptTable
  constructor: ->
    super
    @head.append($('<th class="receipt_status">' + gettext('status') + '</th>'))

  append: (code, name, price, state) ->
    data = [
      @body.children().length + 1,
      code, name, price, state,
    ]
    row = $('<tr>').append(data.map((t) -> $('<td>').text(t)))
    @body.append(row)

  total: (totalPrice) ->
    row = $('<tr>').append(
      $('<th colspan="3">').text(gettext('Total') + ':'),
      $('<th>').text(totalPrice),
      $('<th>'),
    )
    @body.append(row)
