
class BoxesConfig
  url_args:
    # This is used to move urls with arguments from django to JS.
    # It has to satisfy the regexp of the url in django.
    box_id: ''

  urls:
    roller: ''
    box_add: ''
    box_content: ''
    box_hide: ''
    box_print: ''

  enabled: true

  constructor: ->

  box_content_url: (box_id) ->
    url = @urls.box_content
    return url.replace(@url_args.box_id, box_id)

  box_hide_url: (box_id) ->
    url = @urls.box_hide
    return url.replace(@url_args.box_id, box_id)

  box_print_url: (box_id) ->
    url = @urls.box_print
    return url.replace(@url_args.box_id, box_id)

C = new BoxesConfig


createBox = (box_id, description, item_count, item_price, vendor_id, item_type, item_adult) ->
  # Find the hidden template element, clone it and replace the contents.
  box = $(".box_template").clone();
  box.removeClass("box_template");
  box.addClass("box_short")

  $('.box_description', box).text(description)
  $('.box_count', box).text(item_count)
  $('.box_price', box).text(item_price)
  $('.box_type', box).text(item_type)

  if item_adult == "yes"
    $('.box_adult', box).text("K-18")
  else
    $('.box_adult', box).text("-")

  $('.box_vendor_id', box).text(vendor_id)

  $(box).attr('id', box_id)

  return box


# Add a box with name and price set to form contents.
addBox = ->
  onSuccess = (box) ->
    $('#form-errors').empty()
    box = createBox(box.box_id, box.description, box.item_count, box.item_price, box.vendor_id, box.item_type, box.item_adult)
    $('#box-add-form')[0].reset();
    $('#boxes').prepend(box)
    bindBoxEvents($(box))

  onError = (jqXHR, textStatus, errorThrown) ->
    $('#form-errors').empty()
    if jqXHR.responseText
      $('<p>').text(jqXHR.responseText).appendTo($('#form-errors'))

  content =
    description: $("#box-add-description").val()
    name: $("#box-add-itemtitle").val()
    count: $("#box-add-count").val()
    price: $("#box-add-price").val()
    item_type: $("#box-add-itemtype").val()
    adult: $("input[name=box-add-adult]:checked").val()

  $.ajax(
    url: C.urls.box_add
    type: 'POST'
    data: content
    success: onSuccess
    error: onError
  )


hideBox = (box, box_id) ->
  $.ajax(
    url: C.box_hide_url(box_id)
    type: 'POST'
    success: ->
      $(box).remove()
    error: ->
      $(box).show('slow')
  )


printBox = (box, box_id) ->
  printFunc = () ->
    window.open( C.box_content_url(box_id), '_blank' )
    $.ajax(
      url: C.box_print_url(box_id)
      type: 'POST'
      success: ->
        $( '#print_box', box).removeClass("btn-success");
    )

  # Display warning if already printed.
  if isPrinted(box)
    warnAlreadyPrinted( printFunc )
  else
    printFunc();


warnAlreadyPrinted = (print) ->
    result = confirm( gettext( 'This box has been already printed. Are you sure you want to print it again?' ) );
    if result
      print();


isPrinted = (box) ->
  return ! $( '#print_box', box ).hasClass("btn-success");


onPriceChange = ->
  input = $(this)
  formGroup = input.parents(".form-group")

  # Replace ',' with '.' in order to accept numbers with ',' as the period.
  value = input.val().replace(',', '.')
  if value > 400 or value <= 0 or not Number.isConvertible(value)
    formGroup.addClass('has-error')
  else
    formGroup.removeClass('has-error')

  return


bindFormEvents = ->
  $('#box-add-form').bind('submit', ->
    addBox();
    return false;
  )

  return


bindBoxEvents = (boxes) ->
  boxes.each((index, box) ->
    box = $(box)
    box_id = box.attr('id')

    bindBoxHideEvents(box, box_id)
    bindBoxPrintEvents(box, box_id)

    return
  )
  return


bindBoxHideEvents = (box, box_id) ->
  $('.box_button_hide', box).click( ->
    $(box).hide('slow', -> hideBox(box, box_id))
  )

bindBoxPrintEvents = (box, box_id) ->
  $('#print_box', box).click( ->
    printBox(box, box_id)
  )

window.boxesConfig = C
window.addBox = addBox
window.printBox = printBox
window.bindBoxEvents = bindBoxEvents
window.bindFormEvents = bindFormEvents
