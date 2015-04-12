class @VendorInfo
  constructor: (vendor) ->
    @dom = $('<div class="vendor-info-box">')
    @dom.append($('<h3>').text(gettext('Vendor')))

    for attr in ['name', 'email', 'phone', 'id']
      elem = $('<div class="row">')
      elem.append($('<div class="col-xs-2 vendor-info-key">').text(attr))
      elem.append($('<div class="col-xs-10">').text(vendor[attr]))
      @dom.append(elem)
    return

  render: -> @dom
