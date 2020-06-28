class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  constructor: (args..., query) ->
    super
    @vendorTable = Template.vendor_list()
    @vendorList = $(@vendorTable.querySelector("tbody"))
    @query = query
    @badge = new BadgedSelection(@vendorList)

  enter: ->
    super
    @cfg.uiRef.body.append(@vendorTable)
    @badge.enter()

    if @query?
      @onSearchVendor(@query)

  exit: ->
    @badge.exit()

  glyph: -> "user"
  title: -> gettext("Vendor Search")
  inputPlaceholder: -> gettext("Search terms separated by space")

  actions: -> [
    ["", @onSearchVendor]
    [@commands.logout, @onLogout]
  ]

  onSearchVendor: (query) =>
    if query.trim() == ""
      if @badge.currentSelection?
        @vendorList.find("td.badged_index")[@badge.currentSelection].click()
      else
        @vendorList.empty()
    else
      @badge.setBadge(null)
      Api.vendor_find(q: query).done(@onVendorsFound)

  onVendorsFound: (vendors) =>
    @vendorList.empty()
    if vendors.length == 1
      @switcher.switchTo(VendorReport, vendors[0])
      return

    for vendor_, index_ in vendors
      ((vendor, index) =>
        @vendorList.append(Template.vendor_list_item(
          vendor: vendor,
          index: index + 1,
          action: (=> @switcher.switchTo(VendorReport, vendor)),
        ))
      )(vendor_, index_)
    @badge.setBadge(0)
    return
