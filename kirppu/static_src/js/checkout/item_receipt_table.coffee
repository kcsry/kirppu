class @ItemReceiptTable
  constructor: (caption=null, autoNumber=false) ->
    @_table = Templates.render("item_receipt_table",
      caption: caption
      autoNumber: autoNumber
    )
    @_table = $(@_table)
    @body = @_table.find("tbody")

  createRow: (index, code, name, price=null, rounded=false) ->
    row = Templates.render("item_receipt_table_row",
      index: index
      code: code
      name: name
      price: displayPrice(price, rounded)
    )
    return $(row)

  render: () -> @_table
