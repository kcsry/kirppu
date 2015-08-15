
class PriceTagsConfig
  url_args:
    # This is used to move urls with arguments from django to JS.
    # It has to satisfy the regexp of the url in django.
    code: ''

  urls:
    roller: ''
    name_update: ''
    price_update: ''
    item_to_list: ''
    size_update: ''
    item_add: ''
    item_hide: ''
    item_to_print: ''
    all_to_print: ''

  enabled: true
  price_min: 0
  price_max: 400

  constructor: ->

  name_update_url: (code) ->
    url = @urls.name_update
    return url.replace(@url_args.code, code)

  price_update_url: (code) ->
    url = @urls.price_update
    return url.replace(@url_args.code, code)

  item_to_list_url: (code) ->
    url = @urls.item_to_list
    return url.replace(@url_args.code, code)

  size_update_url: (code) ->
    url = @urls.size_update
    return url.replace(@url_args.code, code)

  item_to_print_url: (code) ->
    url = @urls.item_to_print
    return url.replace(@url_args.code, code)

  item_hide_url: (code) ->
    url = @urls.item_hide
    return url.replace(@url_args.code, code)

C = new PriceTagsConfig


createTag = (name, price, vendor_id, code, dataurl, type, adult) ->
  # Find the hidden template element, clone it and replace the contents.
  tag = $(".item_template").clone();
  tag.removeClass("item_template");

  if (type == "short") then tag.addClass("item_short")
  if (type == "tiny") then tag.addClass("item_tiny")

  $('.item_name', tag).text(name)
  $('.item_price', tag).text(price)
  $('.item_head_price', tag).text(price)

  if adult == "yes"
    $('.item_adult_tag', tag).text("K-18")

  $('.item_vendor_id', tag).text(vendor_id)

  $(tag).attr('id', code)
  $('.item_extra_code', tag).text(code)

  $('.barcode_container > img', tag).attr('src', dataurl)


  if listViewIsOn
    tag.addClass('item_list')

  return tag


# Add an item with name and price set to form contents.
addItem = ->
  onSuccess = (items) ->
    $('#form-errors').empty()
    for item in items
      tag = createTag(item.name, item.price, item.vendor_id, item.code, item.barcode_dataurl, item.type, item.adult)
      $('#items').prepend(tag)
      bindTagEvents($(tag))

  onError = (jqXHR, textStatus, errorThrown) ->
    $('#form-errors').empty()
    if jqXHR.responseText
      $('<p>').text(jqXHR.responseText).appendTo($('#form-errors'))

  content =
    name: $("#item-add-name").val()
    price: $("#item-add-price").val()
    suffixes: $("#item-add-suffixes").val()
    tag_type: $("input[name=item-add-type]:checked").val()
    item_type: $("#item-add-itemtype").val()
    adult: $("input[name=item-add-adult]:checked").val()

  $.ajax(
    url: C.urls.item_add
    type: 'POST'
    data: content
    success: onSuccess
    error: onError
  )


deleteAll = ->
  if not confirm(gettext("This will mark all items as printed so they won't be printed again accidentally. Continue?"))
    return

  tags = $('#items > .item_container')
  $(tags).hide('slow')

  $.ajax(
    url:  C.urls.all_to_print
    type: 'POST'
    success: ->
      $(tags).each((index, tag) ->
        code = $(tag).attr('id')
        moveTagToPrinted(tag, code)
      )
    error: ->
      $(tags).show('slow')
  )

  return


listViewIsOn = false;

toggleListView = ->
  listViewIsOn = if listViewIsOn then false else true

  items = $('#items > .item_container')
  if listViewIsOn
    items.addClass('item_list')
  else
    items.removeClass('item_list')


onPriceChange = ->
  input = $(this)
  formGroup = input.parents(".form-group")

  # Replace ',' with '.' in order to accept numbers with ',' as the period.
  value = input.val().replace(',', '.')
  if value > C.price_max or value < C.price_min or not Number.isConvertible(value)
    formGroup.addClass('has-error')
  else
    formGroup.removeClass('has-error')

  return


bindFormEvents = ->
  $('#item-add-form').bind('submit', ->
    addItem();
    return false;
  )

  $('#print_items').click(-> window.print())

  $('#delete_all').click(deleteAll)
  $('#list_view').click(toggleListView)

  $('#item-add-price').change(onPriceChange)

  return


# Bind events for item price editing.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindPriceEditEvents = (tag, code) ->
  $(".item_price", tag).editable(
    C.price_update_url(code),
    indicator: "<img src='" + C.urls.roller + "'>"
    tooltip:   gettext("Click to edit...")
    placeholder: gettext("<em>Click to edit</em>")
    onblur:    "submit"
    style:     "width: 2cm"
    # Update the extra price display for long tags.
    callback:  (value) -> $(".item_head_price", tag).text(value)
  )
  return


# Bind events for item name editing.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindNameEditEvents = (tag, code) ->
  $(".item_name", tag).editable(
    C.name_update_url(code),
    indicator: "<img src='" + C.urls.roller + "'>"
    tooltip:   gettext("Click to edit...")
    placeholder: gettext("<em>Click to edit</em>")
    onblur:    "submit"
    style:     "inherit"
  )
  return


hideItem = (tag, code) ->
  $.ajax(
    url: C.item_hide_url(code)
    type: 'POST'
    success: ->
      $(tag).remove()
    error: ->
      $(tag).show('slow')
  )


bindItemHideEvents = (tag, code) ->
  $('.item_button_hide', tag).click( ->
    $(tag).hide('slow', -> hideItem(tag, code))
  )


moveItemToNotPrinted = (tag, code) ->
  $.ajax(
    url: C.item_to_print_url(code)
    type: 'POST'

    success: (item) ->
      $(tag).remove()

      new_tag = createTag(item.name, item.price, item.vendor_id, item.code, item.barcode_dataurl, item.type, item.adult)
      $(new_tag).hide()
      $(new_tag).appendTo("#items")
      $(new_tag).show('slow')
      bindTagEvents($(new_tag))

    error: (item) ->
      $(tag).show('slow')
  )
  return


moveTagToPrinted = (tag, code) ->
  unbindTagEvents($(tag))

  $('.item_button_printed', tag).click(-> $(tag).hide('slow', -> moveItemToNotPrinted(tag, code)))
  $(tag).prependTo("#printed_items")
  $(tag).addClass("item_list")
  $(tag).show('slow')
  return


moveItemToPrinted = (tag, code) ->
  $.ajax(
    url:  C.item_to_list_url(code)
    type: 'POST'

    success: ->
      moveTagToPrinted(tag, code)

    error: ->
      $(tag).show('slow')
  )
  return


# Bind events for item delete button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemToPrintedEvents = (tag, code) ->
  $('.item_button_printed', tag).click( ->
    $(tag).hide('slow', -> moveItemToPrinted(tag, code))
  )
  return


# Bind events for item delete button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemToNotPrintedEvents = (tag, code) ->
  $('.item_button_printed', tag).click( ->
    $(tag).hide('slow', -> moveItemToNotPrinted(tag, code))
  )
  return


# Bind events for item size toggle button.
# @param tag [jQuery element] An '.item_container' element.
# @param code [String] Barcode string of the item.
bindItemToggleEvents = (tag, code) ->
  setTagType = (tag_type) ->
    if tag_type == "tiny"
      $(tag).addClass('item_tiny')
    else
      $(tag).removeClass('item_tiny')
    if tag_type == "short"
      $(tag).addClass('item_short')
    else
      $(tag).removeClass('item_short')
    return

  getNextType = (tag_type) ->
    tag_type = switch tag_type
      when "tiny" then "short"
      when "short" then "long"
      when "long" then "tiny"
      else "short"
    return tag_type

  onItemSizeToggle = ->
    if $(tag).hasClass('item_short')
      tag_type = "short"
    else if $(tag).hasClass('item_tiny')
      tag_type = "tiny"
    else
      tag_type = "long"

    # Apply next type immediately and backtrack if the ajax call fails.
    new_tag_type = getNextType(tag_type)
    setTagType(new_tag_type)

    $.ajax(
      url:  C.size_update_url(code)
      type: 'POST'
      data:
        tag_type: new_tag_type
      complete: (jqXHR, textStatus) ->
        if textStatus != "success" then setTagType(tag_type)
    )

    return

  $('.item_button_toggle', tag).click(onItemSizeToggle)
  return


# Bind events for a set of '.item_container' elements.
# @param tags [jQuery set] A set of '.item_container' elements.
bindTagEvents = (tags) ->
  tags.each((index, tag) ->
    tag = $(tag)
    code = tag.attr('id')

    if C.enabled
      bindPriceEditEvents(tag, code)
      bindNameEditEvents(tag, code)
    else
      tag.removeClass("item_editable")
    bindItemHideEvents(tag, code)
    bindItemToPrintedEvents(tag, code)
    bindItemToggleEvents(tag, code)

    return
  )
  return


bindListTagEvents = (tags) ->
  tags.each((index, tag) ->
    code = $(tag).attr('id')

    bindItemToNotPrintedEvents(tag, code)

    return
  )
  return


# Unbind events bound by bindTagEvents and bindListTagEvents.
unbindTagEvents = (tags) ->
  tags.each((index, tag) ->

    $('.item_name', tag).unbind('click')
    $('.item_price', tag).unbind('click')
    $('.item_button_toggle', tag).unbind('click')
    $('.item_button_printed', tag).unbind('click')

    return
  )
  return



window.itemsConfig = C
window.addItem = addItem
window.deleteAll = deleteAll
window.bindTagEvents = bindTagEvents
window.bindListTagEvents = bindListTagEvents
window.bindFormEvents = bindFormEvents
