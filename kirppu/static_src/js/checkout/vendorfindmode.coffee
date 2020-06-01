class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  constructor: (args..., query) ->
    super
    @vendorTable = Template.vendor_list()
    @vendorList = $(@vendorTable.querySelector("tbody"))
    @query = query

  enter: ->
    super
    @cfg.uiRef.body.append(@vendorTable)

    if @query?
      @onSearchVendor(@query)

  glyph: -> "user"
  title: -> gettext("Vendor Search")
  inputPlaceholder: -> gettext("Search vendor")

  actions: -> [
    ["", @onSearchVendor]
    [@commands.logout, @onLogout]
  ]

  onSearchVendor: (query) =>
    if query.trim() == ""
      @vendorList.empty()
    else
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
    return
