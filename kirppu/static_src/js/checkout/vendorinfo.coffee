class @VendorInfo
  constructor: (vendor, title=true) ->
    @dom = $('<div class="vendor-info-box">')
    if title
      @dom.append($('<h3>').text(gettext('Vendor')))

    for attr in ['name', 'email', 'phone', 'id']
      elem = $('<div class="row">')
      elem.append($('<div class="col-xs-2 vendor-info-key">').text(attr))
      elem.append($('<div class="col-xs-10">').text(vendor[attr]))
      @dom.append(elem)
    return

  render: -> @dom
