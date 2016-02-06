class @VendorCompensation extends CheckoutMode

  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)
    @vendor = vendor

  title: -> "Vendor Compensation"

  enter: ->
    super
    @cfg.uiRef.codeForm.hide()
    @switcher.setMenuEnabled(false)
    @cfg.uiRef.body.append(new VendorInfo(@vendor).render())

    @buttonForm = $('<form class="hidden-print">').append(@abortButton())
    @cfg.uiRef.body.append(@buttonForm)

    @itemDiv = $('<div>')
    @cfg.uiRef.body.append(@itemDiv)

    Api.item_list(vendor: @vendor.id, state: "SO", include_box_items: true).done(@onGotItems)

  exit: ->
    @cfg.uiRef.codeForm.show()
    @switcher.setMenuEnabled(true)
    super

  confirmButton: ->
    $('<input type="button" class="btn btn-success">')
      .attr('value', 'Confirm')
      .click(@onConfirm)

  abortButton: ->
    $('<input type="button" class="btn btn-default">')
      .attr('value', 'Cancel')
      .click(@onCancel)

  continueButton: ->
    $('<input type="button" class="btn btn-primary">')
      .attr('value', 'Continue')
      .click(@onCancel)

  onGotItems: (items) =>
    @compensableItems = items

    if @compensableItems.length > 0
      table = Templates.render("item_report_table",
        caption: "Sold Items"
        items: @compensableItems
        sum: _.reduce(@compensableItems, ((acc, item) -> acc + item.price), 0)
        topSum: true
      )
      @itemDiv.empty().append(table)
      @buttonForm.empty().append(@confirmButton(), @abortButton())

    else
      @itemDiv.empty().append($('<em>').text('No compensable items'))
      @buttonForm.empty().append(@continueButton())

  onCancel: => @switcher.switchTo(VendorReport, @vendor)

  onConfirm: =>
    @buttonForm.empty()
    nItems = @compensableItems.length
    for i in @compensableItems
      Api.item_compensate(code: i.code).done(=>
        nItems -= 1
        if nItems <= 0 then @onCompensated()
      )

  onCompensated: ->
    @switcher.setPrintable()
    items = @compensableItems
    @compensableItems = []
    for i in items
      i.state = 'CO'
    table = Templates.render("item_report_table",
      caption: "Compensated Items"
      items: items
      sum: _.reduce(@compensableItems, ((acc, item) -> acc + item.price), 0)
      topSum: true
    )
    @itemDiv.empty().append(table)
    @buttonForm.empty().append(@continueButton())
