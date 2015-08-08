class @ClerkLoginMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("clerk_login", @)

  @autoClerk = null

  title: -> "Locked"
  subtitle: -> "Login..."

  enter: ->
    super
    @switcher.setMenuEnabled(false)
    if @constructor.autoClerk?
      @cfg.uiRef.codeInput.val(@constructor.autoClerk)

  actions: -> [[
    "",
    (code) =>
      Api.clerk_login(
        code: code
        counter: @cfg.settings.counterCode
      ).then(@onResultSuccess, @onResultError)
  ]]

  onResultSuccess: (data) =>
    username = data["user"]
    @cfg.settings.clerkName = username
    console.log("Logged in as #{username}.")
    @switcher.setOverseerVisible(data["overseer_enabled"])
    @switcher.setStatsVisible(data["stats_enabled"])
    if data["receipts"]?
      @multipleReceipts(data["receipts"])
    else if data["receipt"]?
      @activateReceipt(data["receipt"])
    else
      @switcher.switchTo(CounterMode)

  onResultError: (jqXHR) =>
    if jqXHR.status == 419
      console.log("Login failed: " + jqXHR.responseText)
      return
    safeAlert("Error:" + jqXHR.responseText)
    return true

  activateReceipt: (receipt) ->
    @switcher.switchTo(CounterMode, receipt)

  multipleReceipts: (receipts) ->
    dialog = new Dialog()
    dialog.title.html('<span class="glyphicon glyphicon-warning-sign text-warning"></span> Multiple receipts active')

    info = $("<div>").text("Please select receipt, which you want to continue.")
    table_body = $("<tbody>")

    @_createReceiptTable(receipts, dialog, table_body)

    table = $('<table class="table table-striped table-hover table-condensed">').append(table_body)
    dialog.body.append(info, table)

    dialog.addPositive().text("Select").click(() =>
      index = table_body.find(".success").data("index")
      if index?
        console.log("Selected #{ 1 + index }: " + receipts[index].start_time)
        @switcher.switchTo(CounterMode, receipts[index])
    )
    dialog.setEnabled(dialog.btnPositive, false)
    dialog.addNegative().text("Cancel").click(() -> console.log("Cancelled receipt selection"))

    # Don't close with keyboard ESC, or by clicking outside dialog.
    dialog.show(
      keyboard: false
      backdrop: "static"
    )

  _createReceiptTable: (receipts, dialog, table_body) ->
    for receipt, i in receipts
      row = $("<tr>")
      row.append(
        $("<td>").text(i + 1),
        $("<td>").text(DateTimeFormatter.datetime(receipt.start_time)),
        $("<td>").text(receipt.total.formatCents()),
        $("<td>").text(receipt.counter),
      )

      # This may not use => version, as `this` id needed.
      row.click(() ->
        table_body.find(".success").removeClass("success")
        $(this).addClass("success")
        dialog.setEnabled(dialog.btnPositive)
      )
      row.data("index", i)
      table_body.append(row)
    return table_body
