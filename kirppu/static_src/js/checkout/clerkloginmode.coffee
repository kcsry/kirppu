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
    @notifySuccess()
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
    table = $ Templates.render("receipt_list_table_simple",
      items: receipts
    )

    # This may not use => version of function, as `this` of the row is needed.
    $("tbody tr", table).click(() ->
      table.find(".success").removeClass("success")
      $(this).addClass("success")
      dialog.setEnabled(dialog.btnPositive)
    )

    dialog.body.append(info, table)

    dialog.addPositive().text("Select").click(() =>
      index = $("tbody", table).find(".success").data("index")
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
