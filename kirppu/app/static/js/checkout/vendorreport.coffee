states =
  compensable:
    SO: gettext('sold')

  returnable:
    BR: gettext('on display')
    ST: gettext('about to be sold')

  other:
    MI: gettext('missing')
    RE: gettext('returned to the vendor')
    CO: gettext('sold and compensated to the vendor')
    AD: gettext('not brought to the event')

tables = [
  [states.compensable, gettext('Compensable Items')]
  [states.returnable,  gettext('Returnable Items')]
  [states.other,       gettext('Other Items')]
]

# Create a new class for the report mode of the vendor.
@vendorReport = (vendor) ->
  class VendorReport extends CheckoutMode

    title: -> gettext("Item Report")

    actions: -> [[
      "", (query) =>
        @switcher.switchTo(VendorFindMode, query)
    ]]

    enter: ->
      super
      @cfg.uiRef.body.append(new VendorInfo(vendor).render())
      Api.item_list(
        vendor: vendor.id
      ).done(@onGotItems)

    onGotItems: (items) =>
      for [states, name] in tables
        table = new ItemReportTable(name)
        @listItems(items, table, states)
        if table.body.children().length > 0
          @cfg.uiRef.body.append(table.render())

    listItems: (items, table, states) ->
      sum = 0
      for i in items when states[i.state]?
        sum += i.price
        table.append(i.code, i.name, displayPrice(i.price), states[i.state])
      if sum > 0
        table.total(displayPrice(sum))
