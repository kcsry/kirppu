class @PrintReceiptTable
  @strCode: gettext("code")
  @strItem: gettext("item")
  @strPrice: gettext("price")
  @strVendor: gettext("vendor")

  constructor: (caption=null)->
    @table = $ Templates.render("receipt_table",
      caption: caption
      vendor: @constructor.strVendor
      code: @constructor.strCode
      item: @constructor.strItem
      price: @constructor.strPrice
    )
    @body = $("tbody", @table)

  @joinedLine: (text="") ->
    Templates.render("receipt_table_row",
      joined: true
      text: text
    )

  @createRow: (vendor, code, name, price, rounded) ->
    Templates.render("receipt_table_row",
      vendor: vendor
      code: code
      name: name
      price: displayPrice(price, rounded)
    )
