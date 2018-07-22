class @VendorList extends ResultTable
  constructor: ->
    super
    @head.append([
      '<th class="receipt_index">#</th>'
      '<th class="receipt_username">%s</th>'.replace("%s", gettext("username"))
      '<th class="receipt_vendor_id">%s</th>'.replace("%s", gettext("id"))
      '<th class="receipt_name">%s</th>'.replace("%s", gettext("name"))
      '<th class="receipt_email">%s</th>'.replace("%s", gettext("email"))
      '<th class="receipt_phone">%s</th>'.replace("%s", gettext("phone"))
    ].map($))

  append: (vendor, index, action) ->
    row = $("<tr>")
    row.addClass('receipt_tr_clickable')
    row.append($("<td>").text(index))

    user = if vendor["username"]?
      vendor["username"]
    else if vendor["owner"]?
      "(via #{vendor["owner"]})"

    row.append($("<td>").text(user))
    row.append(
      for a in ['id', 'name', 'email', 'phone']
        $("<td>").text(vendor[a])
    )
    row.click(action)
    @body.append(row)
