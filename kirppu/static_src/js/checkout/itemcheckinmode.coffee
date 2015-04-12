class @ItemCheckInMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_in", @)

  glyph: -> "import"
  title: -> "Vendor Check-In"

  constructor: (args..., query) ->
    super
    @currentVendor = null

  actions: -> [
    ['', (code) =>
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

        row = @createRow("", data.code, data.name, data.price)
        @receipt.body.prepend(row)
      )
    else
      row = @createRow("", data.code, data.name, data.price)
      @receipt.body.prepend(row)

  onResultError: (jqXHR) =>
    if jqXHR.status == 404
      safeAlert("No such item")
      return
    safeAlert("Error:" + jqXHR.responseText)
    return true
