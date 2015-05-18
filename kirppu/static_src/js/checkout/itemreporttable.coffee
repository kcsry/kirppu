class @ItemReportTable extends ResultTable
  constructor: ->
    super

    @columns = [
      title: gettext('#')
      render: (_, index) -> index + 1
      class: 'receipt_index numeric'
    ,
      title: gettext('code')
      render: (i) -> i.code
      class: 'receipt_code'
    ,
      title: gettext('item')
      render: (i) -> i.name
      class: 'receipt_item'
    ,
      title: gettext('price')
      render: (i) -> displayPrice(i.price)
      class: 'receipt_price numeric'
    ,
      title: gettext('status')
      render: (i) -> i.state_display
      class: 'receipt_status'
    ,
      title: gettext('abandoned')
      render: (i) ->
        if i.abandoned
          "Yes"
        else
          "No"
      class: 'receipt_abandoned'
    ]


    @head.append(
      for c in @columns
        $('<th>').text(c.title).addClass(c.class)
    )

  update: (items) ->
    @body.empty()
    sum = 0
    for item, index in items
      sum += item.price
      row = $('<tr>').append(
        for c in @columns
          $('<td>').text(c.render(item, index)).addClass(c.class)
      )
      @body.append(row)

    @body.append($('<tr>').append(
      $('<th colspan="3">').text(gettext('Total:'))
      $('<th class="receipt_price numeric">').text(displayPrice(sum))
      $('<th>')
      $('<th>')
    ))


class @BoxResultTable extends ResultTable
  columns: [
    "receipt_index numeric"
    ""
    "receipt_price numeric"
    "receipt_count numeric"
    "receipt_count numeric"
    "receipt_count numeric"
  ]

  constructor: ->
    super
    @head.append(@generate("th", [
      "#"
      gettext('description')
      gettext('price')
      gettext('compensable')
      gettext('left')
      gettext('items')
    ], true))
    @head.children().first().addClass("numeric")

  append: (box, index) ->
    row = $("<tr>")
    row.append(@generate("td", [
      index + 1
      box.description
      displayPrice(box.item_price)
      box.items_sold
      box.item_count - box.items_sold - box.items_exit
      box.item_count
    ]))
    @body.append(row)
    return

  update: (boxes) ->
    sum_total = 0
    sum_total_count = 0
    sum_sold = 0
    sum_sold_count = 0
    for box, i in boxes
      @append(box, i)
      sum_total_count += box.item_count
      sum_total += box.item_count * box.item_price
      sum_sold_count += box.items_sold
      sum_sold += box.items_sold * box.item_price

    @body.append($('<tr>').append(
      $('<th colspan="3">').text(gettext('Total:'))
      $('<th class="receipt_price numeric">').text(displayPrice(sum_sold) + " (" + sum_sold_count + ")")
      $('<th>')
      $('<td class="receipt_price numeric">').text(displayPrice(sum_total) + " (" + sum_total_count + ")")
    ))
    return
