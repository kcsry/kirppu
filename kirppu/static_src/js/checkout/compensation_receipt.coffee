class @CompensationReceipt extends CheckoutMode

  constructor: (cfg, switcher, vendor, receipt_id, from_compensation=false) ->
    super(cfg, switcher)
    @vendor = vendor
    @receipt_id = receipt_id
    @_from_compensation = from_compensation
    if typeof(receipt_id) != "number"
      throw new TypeError

  title: -> if @_from_compensation then gettext("Vendor Compensation") else gettext("Compensation Receipt")

  enter: ->
    super
    @cfg.uiRef.codeForm.hide()
    @cfg.uiRef.body.append(new VendorInfo(@vendor).render())

    @buttonForm = $('<form class="hidden-print">').append(@continueButton())
    @cfg.uiRef.body.append(@buttonForm)

    @itemDiv = $('<div>')
    @cfg.uiRef.body.append(@itemDiv)

    Api.receipt_get(
      id: @receipt_id
      type: "compensation"
    ).done(@onGotReceipt)

  continueButton: (type="primary") =>
    $('<input type="button" class="btn btn-' + type + '">')
      .attr('value', 'Continue')
      .click(@onDone)

  exit: ->
    @cfg.uiRef.codeForm.show()
    @switcher.setMenuEnabled(true)
    super

  onGotReceipt: (receipt) =>
    @switcher.setPrintable()

    # TODO: Add subtotal if receipt.extras

    table = Templates.render("item_report_table",
      caption: "Compensated Items"
      items: receipt.items
      sum: receipt.total
      topSum: true
      hide_status: true
    )
    @itemDiv.empty().append(table)

  onDone: =>
    @switcher.switchTo(VendorReport, @vendor)
