tables = [
  # title, included modes, hideInPrint, isExpectedValue (not to be trusted)
  [gettext('Compensable Items'), {SO: 0}, false, true]
  [gettext('Returnable Items'),  {BR: 0, ST: 0}, false, false]
  [gettext('Other Items'),       {MI: 0, RE: 0, CO: 0}, false, false]
  [gettext('Not brought to event'), {AD: 0}, true, false]
]

class @VendorReport extends CheckoutMode
  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)
    @vendor = vendor

  title: -> gettext("Item Report")
  inputPlaceholder: -> gettext("Search vendor")

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
    compensationsButton = $('<input type="button">')
      .addClass('btn btn-default')
      .attr('value', gettext('Compensation receipts'))
      .click(@onShowCompensations)

    @cfg.uiRef.body.append(
      $('<form class="hidden-print">').append(
        compensateButton,
        " ",
        checkoutButton,
        " ",
        abandonButton,
        " ",
        compensationsButton
      )
    )

    Api.item_list(
      vendor: @vendor.id
    ).done((items) =>
      Api.box_list(
        vendor: @vendor.id
      ).done((boxes) =>
        Api.receipt_compensated(
          vendor: @vendor.id
        ).done((compensations) =>
          @onGotItems(items, boxes, compensations)
        )
      )
    )

  onGotItems: (items, boxes, compensations) =>
    @switcher.setPrintable()

    @_compensations = compensations

    for [name, states, hidePrint, isExpectedSum] in tables
      matchingItems = (i for i in items when states[i.state]?)
      rendered_table = Templates.render("item_report_table",
         caption: name
         items: matchingItems
         sum: _.reduce(matchingItems, ((acc, item) -> acc + item.price), 0)
         hidePrint: hidePrint
         isExpectedSum: isExpectedSum
         hideSumInPrint: true
      )
      @cfg.uiRef.body.append(rendered_table)

    if boxes.length > 0
      [sum_brought_count, sum_brought, sum_sold_count, sum_sold] = [0, 0, 0, 0]
      for box in boxes
        sum_brought_count += box.items_brought_total
        sum_brought += box.items_brought_total * box.item_price
        sum_sold_count += box.items_sold
        sum_sold += box.items_sold * box.item_price

      rendered_table = Templates.render("box_report_table",
        caption: gettext("Boxes")
        items: boxes
        sum_brought_count: sum_brought_count
        sum_brought: sum_brought
        sum_sold_count: sum_sold_count
        sum_sold: sum_sold
        hideSumInPrint: true
      )

      # Insert box list before Not Brought list.
      @cfg.uiRef.body.children().last().before(rendered_table)
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

  onShowCompensations: =>
    dlg = new Dialog()
    dlg.title.text(gettext("Compensation receipts"))

    # TODO: customized Dialog class for listing things?
    table = $ Templates.render("receipt_list_table_compensations",
      items: @_compensations
    )

    dlg.addNegative().text(gettext("Close")).addClass("btn-primary")
    buttonPositive = dlg.addPositive().text(gettext("Show"))

    $("tbody tr", table).click(() ->
      table.find(".success").removeClass("success")
      $(this).addClass("success")
      dlg.setEnabled(buttonPositive)
    )

    buttonPositive.click(() =>
      selected = $("tbody", table).find(".success")
      index = selected.data("index")
      selected_id = selected.data("id")
      receipt_id = @_compensations[index].id
      if receipt_id != selected_id
        throw new "ID mismatch!"
      @switcher.switchTo(CompensationReceipt, @vendor, receipt_id)
    )

    dlg.setEnabled(buttonPositive, false)

    dlg.body.append(table)
    dlg.show()
