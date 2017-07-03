class @ItemCheckInMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_in", @)

  glyph: -> "import"
  title: -> gettext("Vendor Check-In")

  constructor: (args..., query) ->
    super
    @currentVendor = null
    @itemIndex = 1

  actions: -> [
    ['', (code) =>
      code = fixToUppercase(code)
      Api.item_checkin(
        code: code
      ).then(@onResultSuccess, @onResultError)
    ]
    [@commands.logout, @onLogout]
  ]

  onResultSuccess: (data) =>
    if data.vendor != @currentVendor
      @currentVendor = data.vendor
      Api.vendor_get(id: @currentVendor).done((vendor) =>
        vendorInfoRow = $('<tr><td colspan="4">')
        $('td', vendorInfoRow).append(new VendorInfo(vendor).render())
        @receipt.body.prepend(vendorInfoRow)

        row = @createRow(@itemIndex++, data.code, data.name, data.price)
        @receipt.body.prepend(row)
      ).fail(@onResultError)
    else
      row = @createRow(@itemIndex++, data.code, data.name, data.price)
      @receipt.body.prepend(row)
    @notifySuccess()

  onResultError: (jqXHR) =>
    if jqXHR.status == 404
      safeAlert(gettext("No such item"))
      return
    safeAlert(gettext("Error: %s").replace("%s", jqXHR.responseText))
    return true
