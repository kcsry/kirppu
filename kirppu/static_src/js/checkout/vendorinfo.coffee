class @VendorInfo
  constructor: (vendor, title=true) ->
    @_vendor = vendor
    @_title = title
    return

  render: -> Templates.render("vendor_info",
    vendor: @_vendor,
    title: @_title,
  )
