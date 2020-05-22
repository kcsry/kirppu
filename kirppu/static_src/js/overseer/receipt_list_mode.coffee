class @ReceiptFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("receipt_list", @)

  constructor: ->
    super
    @receiptList = new ReceiptList()

  enter: ->
    super
    refresh = new RefreshButton(=> Api.receipt_pending().done(@onResult))
    @cfg.uiRef.body.empty()
    @cfg.uiRef.body.append(refresh.render())
    @cfg.uiRef.body.append(@receiptList.render())
    refresh.refresh()

  glyph: -> "list-alt"
  title: -> gettext("Receipt List")
  subtitle: -> null

  onResult: (receipts) =>
    @receiptList.body.empty()
    for receipt, index in receipts
      row = @receiptList.append(receipt, index + 1)
      row.on("click", @_showReceiptFn(receipt.id))
    if receipts.length == 0
      @receiptList.no_results()

  _showReceiptFn: (receiptId) =>
    () =>
      dialog = new Dialog()
      dialog.addPositive().text("Ok")
      dialog.title.text(gettext("Receipt details"))

      Api.receipt_get(id: receiptId).then(
        (data) =>
          result = Template.receipt_info(receipt: data)
          dialog.body.append(result)

        (jqXHR) =>
          dialog.body.text(jqXHR.responseText)
      )
      dialog.show()
