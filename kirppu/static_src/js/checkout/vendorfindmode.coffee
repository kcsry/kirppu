class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  constructor: (args..., query) ->
    super
    @vendorList = new VendorList()
    @query = query

  enter: ->
    super
    @cfg.uiRef.body.append(@vendorList.render())

    if @query?
      Api.vendor_find(q: @query).done(@onVendorsFound)

  glyph: -> "user"
  title: -> "Vendor Search"
  inputPlaceholder: -> "Search vendor"

  actions: -> [
    ["", (query) => Api.vendor_find(q: query).done(@onVendorsFound)]
    [@commands.logout, @onLogout]
  ]

  onVendorsFound: (vendors) =>
    @vendorList.body.empty()
    if vendors.length == 1
      @switcher.switchTo(VendorReport, vendors[0])
      return

    for vendor_, index_ in vendors
      ((vendor, index) =>
        @vendorList.append(
          vendor,
          index + 1,
          (=> @switcher.switchTo(VendorReport, vendor)),
        )
      )(vendor_, index_)
    return

