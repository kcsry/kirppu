class @ReceiptFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("receipt_list", @)

  constructor: ->
    super
    @receiptTable = Template.overseer_receipt_table()
    @receiptList = $(@receiptTable.querySelector("tbody"))

  enter: ->
    super
    refresh = new RefreshButton(=> Api.receipt_pending().done(@onResult))
    @cfg.uiRef.body.empty()
    @cfg.uiRef.body.append(refresh.render())
    @cfg.uiRef.body.append(@receiptTable)
    refresh.refresh()

  glyph: -> "list-alt"
  title: -> gettext("Receipt List")
  subtitle: -> null

  onResult: (receipts) =>
    @receiptList.empty()
    for receipt, index in receipts
      row = $ Template.overseer_receipt_table_item(
        item: receipt
        index: index + 1
      )
      row.on("click", @_showReceiptFn(receipt.id))
      @receiptList.append(row)
    if receipts.length == 0
      @receiptList.append(Template.overseer_receipt_table_no_results())

  _showReceiptFn: (receiptId) =>
    () =>
      dialog = new Dialog()
      dialog.addPositive().text(gettext("Ok"))
      dialog.title.text(gettext("Receipt details"))

      Api.receipt_get(id: receiptId).then(
        (data) =>
          result = Template.receipt_info(receipt: data)
          dialog.body.append(result)

        (jqXHR) =>
          dialog.body.text(jqXHR.responseText)
      )
      dialog.show()
