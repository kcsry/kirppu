class @ReceiptList extends ResultTable

  columns: [
    "receipt_index numeric"  # index
    ""                       # counter
    ""                       # clerk
    ""                       # start time
    "receipt_price numeric"  # total
    ""                       # status
  ]

  constructor: ->
    super
    @head.append(@generate("th", [
      "#"
      gettext('counter')
      gettext('clerk')
      gettext('start time')
      gettext('total')
      gettext('status')
    ], true))

  append: (item, index) ->
    row = $("<tr class='receipt_tr_clickable'>")
    row.append(@generate("td", [
      index
      item.counter
      item.clerk.print
      DateTimeFormatter.datetime(item.start_time)
      displayPrice(item.total)
      item.status_display
    ]))
    @body.append(row)
    return row

  no_results: () ->
    @body.append($("<tr>").append([
      $('<td>')
      $('<td colspan="5">').text(gettext("No results."))
    ]))
