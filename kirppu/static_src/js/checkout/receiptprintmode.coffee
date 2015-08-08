class @ReceiptPrintMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("reports", @)

  @strTotal: "Total"
  @strTitle: "Receipt"
  @strTitleFind: "Find receipt"
  @strSell: "%d, served by %c"

  constructor: (cfg, switcher, receiptData) ->
    super
    @hasReceipt = receiptData?
    @receipt = new PrintReceiptTable()
    @initialReceipt = receiptData

  enter: ->
    super
    @cfg.uiRef.body.append(@receipt.render())
    if @initialReceipt?
      @renderReceipt(@initialReceipt)
      window.print()
    return

  glyph: -> "list-alt"
  title: -> if not @hasReceipt then @constructor.strTitleFind else @constructor.strTitle
  subtitle: -> ""
  commands: ->
    print: ["print", "Print receipt / return"]

  actions: -> [
    ["", @findReceipt]
    [@commands.logout, @onLogout]
    [@commands.print, @onReturnToCounter]
  ]

  findReceipt: (code) =>
    Api.receipt_get(item: code).then(
      (data) =>
        @renderReceipt(data)
      () =>
        safeAlert("Item not found in receipt!")
    )

  renderReceipt: (receiptData) ->
    @receipt.body.empty()
    for item in receiptData.items
      if item.action != "ADD"
        continue
      row = PrintReceiptTable.createRow(item.vendor, item.code, item.name, item.price, false)
      @receipt.body.append(row)

    replacer = (s) ->
      switch s[1]
        when 'd' then DateTimeFormatter.datetime(receiptData.sell_time)
        when 'c' then receiptData.clerk.print
        else s[1]

    sellFmt = /%[dc%]/g
    sellStr = @constructor.strSell.replace(sellFmt, replacer)

    @receipt.body.append(row) for row in [
      @constructor.middleLine
      PrintReceiptTable.createRow("", "", @constructor.strTotal, receiptData.total, true)
      PrintReceiptTable.joinedLine(sellStr)
    ].concat(@constructor.tailLines)

    @hasReceipt = true
    @switcher.updateHead()
    return


  onReturnToCounter: =>
    @switcher.switchTo(CounterMode)

  @middleLine: PrintReceiptTable.joinedLine()
  @tailLines: [
    PrintReceiptTable.joinedLine()
  ]
