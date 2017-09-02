class @VendorCheckoutMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_out", @)

  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)

    @vendorId = if vendor? then vendor.id else null

    @receipt = new ItemReceiptTable(gettext('Returned items'), true)
    @lastItem = new ItemReceiptTable()
    @remainingItems = new ItemReceiptTable(gettext('Remaining items'), true)

    @_asyncReturnedCodes = []
    @_vendorInfoAdded = 0  # 0=No, 1=Pending, 2=Done

  enter: ->
    super

    @cfg.uiRef.body.prepend(@remainingItems.render())
    lastItem = @lastItem.render()
    $(".receipt_item", lastItem).text("last returned item")
    @cfg.uiRef.body.prepend(lastItem)
    if @vendorId? then do @_addVendorInfo

  glyph: -> "export"
  title: -> gettext("Vendor Check-Out")

  actions: -> [
    ['', @addCodeToReturn]
    [@commands.logout, @onLogout]
  ]


  addCodeToReturn: (code) =>
    # Add code to pending list and depending on current UI state, either
    # fetch the vendor info and item list, do nothing or process the pending list.
    # List processing may not be done before vendor info and item list has been
    # added, as otherwise some items are not removed from "remaining items" list.
    @_asyncReturnedCodes.push(code)
    switch @_vendorInfoAdded
      when 0 then @_addVendorInfo()
      #when 1: Wait for completion. Code is added to list so it is processed later.
      when 2 then @_processList()
    return


  _addVendorInfo: ->
    @_vendorInfoAdded = 1
    if @vendorId?
      request = id: @vendorId
    else
      request = code: @_asyncReturnedCodes[0]

    next = () => Api.item_list(
      vendor: @vendorId
      include_box_items: true
    ).done(@_onGotItems)

    Api.vendor_get(request).done((vendor) =>
      @cfg.uiRef.body.prepend(
        $('<input type="button">')
          .addClass('btn btn-primary')
          .attr('value', gettext('Open Report'))
          .click(=> @switcher.switchTo(VendorReport, vendor))
      )
      @cfg.uiRef.body.prepend(new VendorInfo(vendor).render())
      if not @vendorId?
        @vendorId = vendor.id
        next()
    )

    if @vendorId?
      next()


  _onGotItems: (items) =>
    remaining = {BR: 0, ST: 0, MI: 0}
    for item in items when remaining[item.state]?
      row = @createRow("", item.code, item.name, item.price)
      @remainingItems.body.prepend(row)

    returned = {RE: 0, CO: 0}
    for item in items when returned[item.state]?
      row = @createRow("", item.code, item.name, item.price)
      @receipt.body.prepend(row)

    @_vendorInfoAdded = 2
    @_processList()


  _processList: ->
    if @_asyncReturnedCodes.length > 0
      codeToReturn = @_asyncReturnedCodes.shift()
      @_doReturnItem(codeToReturn)


  _doReturnItem: (code) =>
    if not @vendorId?
      # Need vendorId before the item is actually returned.
      throw "IllegalState"

    code = fixToUppercase(code)
    Api.item_checkout(
      code: code
      vendor: @vendorId
    ).then(
      @onCheckedOut

      (jqXHR) ->
        switch jqXHR.status
          when 404 then message = gettext("Item not found: %s").replace("%s", code)
          when 423 then message = jqXHR.responseText
          else message = gettext("Error: %s").replace("%s", jqXHR.responseText)
        safeAlert(message)
    )


  onCheckedOut: (item) =>
    if item._message?
      safeWarning(item._message)

    # Move just returned item to "Last returned item" part from "remaining items" list.
    returnable_item = $('#' + item.code, @remainingItems.body)
    if returnable_item.size() == 0
      # Item was not in "remaining" list, but it was still returned. (Transition from state AD.)
      console.warn("Item not found in list of remaining items: " + item.code)
      returnable_item = @createRow("", item.code, item.name, item.price)
    @receipt.body.prepend(returnable_item.clone())

    # Add the just returned item to "last item" list.
    @lastItem.body.empty().append(returnable_item)
    @notifySuccess()
    @_processList()
    return
