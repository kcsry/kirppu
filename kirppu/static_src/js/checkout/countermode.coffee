class @CounterMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("customer_checkout", @)

  constructor: (args..., modeArgs) ->
    super(args...)
    @_receipt = new ReceiptData()
    @receiptSum = new ReceiptSum()
    if modeArgs?
      @restoreReceipt(modeArgs)
    @receipt.body.attr("id", "counter_receipt")

  glyph: -> "euro"
  title: -> gettext("Checkout")
  commands: ->
    abort: ["abort", gettext("Abort receipt")]
    suspend: ["suspend", gettext("Suspend active receipt")]
    print: ["print", gettext("Print receipt / return")]

  actions: -> [
    [@commands.abort,                 @onAbortReceipt]
    [@commands.suspend,               @onSuspendReceipt]
    [@commands.print,                 @onPrintReceipt]
    [@commands.logout,                @onLogout]
    [@cfg.settings.payPrefix,         @onPayReceipt]
    [@cfg.settings.removeItemPrefix,  @onRemoveItem]
    ["",                              @onAddItem]
  ]

  _box_exp: /^(?:(\d+)\s*[*x.]\s*)?box\s*(\d+)$/

  _match_box_exp: (code) ->
    box_match = @_box_exp.exec(code)
    if box_match
      box_item_count = if box_match[1]? then Number.parseInt(box_match[1]) else null
      box_number = Number.parseInt(box_match[2])
      if Number.isNaN(box_item_count) or Number.isNaN(box_number)
        throw new Error("NaN")
      return (
        number: box_number
        item_count: box_item_count
        input: code
      )
    return null

  _create_box_arg: (box) ->
    r = box_number: box.number
    if box.item_count?
      r.box_item_count = box.item_count
    return r

  enter: ->
    @cfg.uiRef.body.append(@receiptSum.render())
    super
    @_setSum()

  addRow: (code, item, price, rounded=false) ->
    if code?
      @_receipt.rowCount++
      index = @_receipt.rowCount
      if price? and price < 0 then index = -index
    else
      code = ""
      index = ""

    row = @createRow(index, code, item, price, rounded)
    @receipt.body.prepend(row)
    if @_receipt.isActive()
      @_setSum(@_receipt.total)
    return row

  onAddItem: (code) =>
    code = code.trim()
    if code == "" then return

    box = @_match_box_exp(code)
    if box
      if not @_receipt.isActive()
        Api.box_find(box_number: box.number).then(
          () => @startReceipt(null, box)
          (jqXHR) => @_onInitialItemFailed(jqXHR, null, box)
        )
      else
        @reserveItem(null, box)

    else

      code = fixToUppercase(code)
      if not @_receipt.isActive()
        Api.item_find(code: code, available: true).then(
          () => @startReceipt(code)
          (jqXHR) => @_onInitialItemFailed(jqXHR, code)
        )
      else
        @reserveItem(code)

  showError: (status, text, code, box) =>
    switch status
      when 0 then errorMsg = gettext("Network disconnected!")
      when 404 then errorMsg =
        if code? then gettext("Item is not registered.") else gettext("Invalid box number.")
      when 409 then errorMsg = text
      when 423 then errorMsg = text
      else errorMsg = gettext("Error %s.").replace("%s", status)

    data = if code? then code else box.input
    safeAlert(errorMsg + ' ' + data)

  restoreReceipt: (receipt) ->
    @switcher.setMenuEnabled(false)
    Api.receipt_activate(id: receipt.id).then(
      (data) => @_startOldReceipt(data)
      () =>
        alert(gettext("Could not restore receipt!"))
        @switcher.setMenuEnabled(true)
    )

  _startOldReceipt: (data) ->
    throw "Still active receipt!" if @_receipt.isActive()

    @_receipt.start(data)
    @_receipt.total = data.total

    @receipt.body.empty()
    for item in data.items
      price = if item.action == "DEL" then -item.price else item.price
      @addRow(item.code, item.name, price)
    @_setSum(@_receipt.total)

  _onInitialItemFailed: (jqXHR, code, box=null) =>   # TODO
    if jqXHR.status == 423
      # Locked. Is it suspended?
      if jqXHR.responseJSON? and jqXHR.responseJSON.receipt?
        receipt = jqXHR.responseJSON.receipt
        dialog = new Dialog()
        dialog.title.text(gettext("Continue suspended receipt?"))
        table = Templates.render("receipt_info", receipt: receipt)
        dialog.body.append(table)
        dialog.addPositive().text(gettext("Continue")).click(() =>
          console.log("Continuing receipt #{receipt.id}")
          Api.receipt_continue(code: code).then((data) =>
            @_startOldReceipt(data)
          )
        )
        dialog.addNegative().text(gettext("Cancel"))
        dialog.show(
          keyboard: false
          backdrop: "static"
        )
        return
    # else:
    @showError(jqXHR.status, jqXHR.responseText, code, box)

  startReceipt: (code, box=null) ->
    @_receipt.start()

    # Changes to other modes now would result in fatal errors.
    @switcher.setMenuEnabled(false)

    Api.receipt_start().then(
      (data) =>
        @_receipt.data = data
        @receipt.body.empty()
        @_setSum()
        @reserveItem(code, box)

      (jqHXR) =>
        safeAlert("Could not start receipt! " + jqHXR.responseText)
        # Rollback.
        @_receipt.end()
        @switcher.setMenuEnabled(true)
        return true
    )

  _setSum: (sum=0, ret=null) ->
    sum_fmt = CURRENCY.raw[0] + (sum).formatCents() + CURRENCY.raw[1]
    if ret?
      text = dPrintF(gettext("Total: %t / Return: %r"),
        t: sum_fmt
        r: CURRENCY.raw[0] + (ret).formatCents() + CURRENCY.raw[1]
      )
    else
      text = gettext("Total: %t").replace("%t", sum_fmt)

    @receiptSum.set(text)
    @receiptSum.setEnabled(@_receipt.isActive())

  reserveItem: (code, box) ->
    if (!code? and !box?) or (code? and box?)
      throw Error("Invalid arguments")

    if code?
      Api.item_reserve(code: code).then(
        (data) =>
          if data._message?
            safeWarning(data._message)
          @_receipt.total += data.price

          if Math.abs(data.total - @_receipt.total) >= 1
            console.error("Inconsistency: " + @_receipt.total + " != " + data.total)

          @addRow(data.code, data.name, data.price)
          @notifySuccess()

        (jqXHR) =>
          @showError(jqXHR.status, jqXHR.responseText, code)
          return true
      )

    else
      Api.box_item_reserve(
        @_create_box_arg(box)
      ).then(
        (data) =>
          @_receipt.total += data.item_price * data.changed

          if Math.abs(data.total - @_receipt.total) >= 1
            console.error("Inconsistency: " + @_receipt.total + " != " + data.total)

          for code in data.item_codes
            @addRow(code, data.item_name, data.item_price)
          @notifySuccess()

        (jqXHR) =>
          @showError(jqXHR.status, jqXHR.responseText, code, box)
          return true
      )

  onRemoveItem: (code) =>
    unless @_receipt.isActive() then return

    box = @_match_box_exp(code)
    if !box?

      code = fixToUppercase(code)
      Api.item_release(code: code).then(
        (data) =>
          @_receipt.total -= data.price

          if Math.abs(data.total - @_receipt.total) >= 1
            console.error("Inconsistency: " + @_receipt.total + " != " + data.total)

          @addRow(data.code, data.name, -data.price)
          @notifySuccess()

        (jqXHR) =>
          if jqXHR.status == 404
            safeAlert(gettext("Item not found on receipt: %s").replace("%s", code))
          else
            safeAlert(jqXHR.responseText)
          return true
      )

    else

      Api.box_item_release(
        @_create_box_arg(box)
      ).then(
        (data) =>
          @_receipt.total -= data.item_price * data.changed

          if Math.abs(data.total - @_receipt.total) >= 1
            console.error("Inconsistency: " + @_receipt.total + " != " + data.total)

          for code in data.item_codes
            @addRow(code, data.item_name, -data.item_price)
          @notifySuccess()

        (jqXHR) =>
          if jqXHR.status == 404
            safeAlert(gettext("Item not found on receipt: %s").replace("%s", code))
          else
            safeAlert(jqXHR.responseText)
          return true
      )


  onPayReceipt: (input) =>
    unless Number.isConvertible(input)
      unless input == @cfg.settings.quickPayExtra
        safeWarning("Number not understood. The format must be like: #{@cfg.settings.payPrefix}0.00")
        return
      else
        # Quick pay.
        input = @_receipt.total

    else
      # If decimal separator is supplied, ensure dot and expect euros.
      input = input.replace(",", ".")
      input = (input - 0) * 100

      # Round the number to integer just to be sure it is whole cents (and no parts of it).
      # This should differ maximum of epsilon from previous line.
      input = Math.round(input)

    if input < @_receipt.total
      safeAlert(gettext("Not enough given money!"))
      return

    if input > @cfg.settings.purchaseMax * 100
      safeAlert(gettext("Not accepting THAT much money!"))
      return

    # Convert previous payment calculations from success -> info,muted
    @receipt.body.children(".receipt-ending").removeClass("success").addClass("info text-muted")

    # Add (new) payment calculation rows.
    return_amount = input - @_receipt.total
    row.addClass("success receipt-ending") for row in [
      @addRow(null, gettext("Subtotal"), @_receipt.total, true),
      @addRow(null, gettext("Cash"), input),
      @addRow(null, gettext("Return"), return_amount, true),
    ]

    # Also display the return amount in the top.
    @_setSum(@_receipt.total, return_amount.round5())

    # End receipt only if it has not been ended.
    unless @_receipt.isActive() then return
    Api.receipt_finish(id: @_receipt.data.id).then(
      (data) =>
        @_receipt.end(data)
        console.log(@_receipt)

        # Mode switching is safe to use again.
        @switcher.setMenuEnabled(true)
        @receiptSum.setEnabled(false)

      (jqXHR) =>
        safeAlert("Error ending receipt! " + jqXHR.responseText)
        return true
    )

  onAbortReceipt: =>
    unless @_receipt.isActive() then return

    Api.receipt_abort(id: @_receipt.data.id).then(
      (data) =>
        @_receipt.end(data)
        console.log(@_receipt)

        @addRow(null, gettext("Aborted"), null).addClass("danger")
        # Mode switching is safe to use again.
        @switcher.setMenuEnabled(true)
        @receiptSum.setEnabled(false)
        @notifySuccess()

      (jqXHR) =>
        safeAlert("Error ending receipt! " + jqXHR.responseText)
        return true
    )

  onSuspendReceipt: =>
    unless @_receipt.isActive() then return

    dialog = new Dialog()
    dialog.title.text(gettext("Suspend receipt?"))
    form = Templates.render("receipt_suspend_form")
    dialog.body.append(form)

    dialog.addPositive().text(gettext("Suspend")).click(() =>
      Api.receipt_suspend(note: $("#suspend_note", dialog.body).val()).then(
        (receipt) =>
          @_receipt.end(receipt)

          @addRow(null, gettext("Suspended"), null).addClass("warning")
          @switcher.setMenuEnabled(true)
          @receiptSum.setEnabled(false)
          @notifySuccess()

        () => safeAlert("Error suspending receipt!")
      )
    )
    dialog.addNegative().text(gettext("Cancel"))
    dialog.show()

  onPrintReceipt: =>
    unless @_receipt.data?
      safeAlert(gettext("No receipt to print!"))
      return
    else if @_receipt.isActive()
      safeAlert(gettext("Cannot print while receipt is active!"))
      return
    else unless @_receipt.isFinished()
      safeAlert(gettext("Cannot print. The receipt is not in finished state!"))
      return

    Api.receipt_get(id: @_receipt.data.id).then(
      (receipt) =>
        @switcher.switchTo( ReceiptPrintMode, receipt )

      () =>
        safeAlert(gettext("Error printing receipt!"))
        return true
    )

  onLogout: =>
    if @_receipt.isActive()
      safeAlert(gettext("Cannot logout while receipt is active!"))
      return

    super


# Class for holding in some some of receipt information.
# @private
class ReceiptData
  constructor: ->
    @start(null)
    @active = false

  isActive: -> @active
  isFinished: -> if @data? then @data.status == "FINI" else false
  start: (data=null) ->
    @active = true
    @rowCount = 0
    @total = 0
    @data = data

  end: (data=null) ->
    @active = false
    @data = data
