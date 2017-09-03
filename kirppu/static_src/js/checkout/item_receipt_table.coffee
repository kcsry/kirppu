class @ItemReceiptTable
  # @param {Object} options
  # @param {str} [optional] options.caption
  # @param {bool} [optional] options.autoNumber
  constructor: (options=null) ->
    options = Object.assign(
      caption: null
      autoNumber: false
      splitTitle: false
      , options
    )

    @_table = Templates.render("item_receipt_table", options)
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

  row: (args) ->
    row = Templates.render("item_receipt_table_row", args)
    return $(row)

  render: () -> @_table
