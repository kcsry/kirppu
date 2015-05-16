tables = [
  # title, included modes, hideInPrint
  [gettext('Compensable Items'), {SO: 0}, false]
  [gettext('Returnable Items'),  {BR: 0, ST: 0}, false]
  [gettext('Other Items'),       {MI: 0, RE: 0, CO: 0}, false]
  [gettext('Not brought to event'), {AD: 0}, true]
]

class @VendorReport extends CheckoutMode
  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)
    @vendor = vendor

  title: -> gettext("Item Report")
  inputPlaceholder: -> "Search vendor"

  actions: -> [
    ["", (query) => @switcher.switchTo(VendorFindMode, query)]
    [@commands.logout, @onLogout]
  ]

  enter: ->
    super
    @cfg.uiRef.body.append(new VendorInfo(@vendor).render())
    compensateButton = $('<input type="button">')
      .addClass('btn btn-primary')
      .attr('value', gettext('Compensate'))
      .click(@onCompensate)
    checkoutButton = $('<input type="button">')
      .addClass('btn btn-primary')
      .attr('value', gettext('Return Items'))
      .click(@onReturn)
    abandonButton = $('<input type="button">')
      .addClass('btn btn-primary')
      .attr('value', gettext('Abandon All Items Currently On Display'))
      .click(@onAbandon)
    @cfg.uiRef.body.append(
      $('<form class="hidden-print">').append(
        compensateButton,
        " ",
        checkoutButton,
        " ",
        abandonButton,
      )
    )

    Api.item_list(
      vendor: @vendor.id
    ).done((items) =>
      Api.box_list(
        vendor: @vendor.id
      ).done((boxes) => @onGotItems(items, boxes))
    )

  onGotItems: (items, boxes) =>
    for [name, states, hidePrint] in tables
      matchingItems = (i for i in items when states[i.state]?)
      table = new ItemReportTable(name)
      table.update(matchingItems)
      rendered_table = table.render()
      if hidePrint then rendered_table.addClass('hidden-print')
      @cfg.uiRef.body.append(rendered_table)

    if boxes.length > 0
      table = new BoxResultTable(gettext("Boxes"))
      table.update(boxes)
      rendered_table = table.render()
      @cfg.uiRef.body.append(rendered_table)
    return

  onCompensate: => @switcher.switchTo(VendorCompensation, @vendor)
  onReturn: =>     @switcher.switchTo(VendorCheckoutMode, @vendor)
  onAbandon: =>
    r = confirm(gettext("1) Have you asked for the vendor's signature AND 2) Are you sure you want to mark all items on display or missing abandoned?"))
    if r
      Api.items_abandon(
        vendor: @vendor.id
      ).done(=> @switcher.switchTo(VendorReport, @vendor))
    return

