class @ReceiptFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("receipt_list", @)

  constructor: ->
    super
    @receiptList = new ReceiptList()

  enter: ->
    super
    refresh = new RefreshButton(=> Api.receipt_list().done(@onResult))
    @cfg.uiRef.body.empty()
    @cfg.uiRef.body.append(refresh.render())
    @cfg.uiRef.body.append(@receiptList.render())
    refresh.refresh()

  glyph: -> "list-alt"
  title: -> "Receipt List"
  subtitle: -> null

  onResult: (receipts) =>
    @receiptList.body.empty()
    for receipt, index in receipts
      @receiptList.append(receipt, index + 1)
    if receipts.length == 0
      @receiptList.no_results()
