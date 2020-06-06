class @PrintReceiptTable
  constructor: (caption=null)->
    @table = $ Template.receipt_table(
      caption: caption
    )
    @body = $("tbody", @table)

  @joinedLine: (text="") ->
    Template.receipt_table_row(
      joined: true
      text: text
    )

  @createRow: (vendor, code, name, price, rounded) ->
    Template.receipt_table_row(
      vendor: vendor
      code: code
      name: name
      price: displayPrice(price, rounded)
    )
