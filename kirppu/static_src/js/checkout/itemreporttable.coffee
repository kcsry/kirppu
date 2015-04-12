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
