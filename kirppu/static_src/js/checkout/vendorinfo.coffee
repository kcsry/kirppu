class @VendorInfo
  constructor: (vendor, title=true) ->
    @_vendor = vendor
    @_vendor.terms_accepted_str = if vendor.terms_accepted? then DateTimeFormatter.datetime(vendor.terms_accepted) else ""
    @_title = title
    return

  render: -> Templates.render("vendor_info",
    vendor: @_vendor,
    title: @_title,
    text:
      name: gettext("name")
      email: gettext("email")
      phone: gettext("phone")
      id: gettext("id")
      terms_accepted_str: gettext("terms accepted?")
  )
