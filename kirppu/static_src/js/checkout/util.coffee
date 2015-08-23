@CURRENCY =
  css: ["", ""]
  html: ["", ""]
  raw: ["", ""]

@displayPrice = (price, rounded=false) ->
  if price?
    if Number.isInteger(price)
      price_str = CURRENCY.raw[0] + price.formatCents() + CURRENCY.raw[1]
    else
      price_str = price
      rounded = false
  else
    price_str = ""
    rounded = false

  if rounded and price.round5() != price
    rounded_str = CURRENCY.raw[0] + price.round5().formatCents() + CURRENCY.raw[1]
    price_str = "#{ rounded_str } (#{ price_str })"

  return price_str

@displayState = (state) ->
  {
    SO: gettext('sold')
    BR: gettext('on display')
    ST: gettext('about to be sold')
    MI: gettext('missing')
    RE: gettext('returned to the vendor')
    CO: gettext('sold and compensated to the vendor')
    AD: gettext('not brought to the event')
  }[state]

# Round the number to closest modulo 5.
#
# @return Integer rounded to closest 5.
Number.prototype.round5 = ->
  modulo = this % 5

  # 2.5 == split-point, i.e. half of 5.
  if modulo >= 2.5
    return this + (5 - modulo)
  else
    return this - modulo

# Internal flag to ensure that blinking is finished before the error text can be removed.
stillBlinking = false

# Instance of the sound used for barcode errors.
@UtilSound =
  error: null

# Display safe alert error message.
#
# @param message [String] Message to display.
# @param blink [Boolean, optional] If true (default), container is blinked.
@safeAlert = (message, blink=true) ->
  if UtilSound.error?
    UtilSound.error.play()
  safeDisplay(CheckoutConfig.uiRef.errorText, message, if blink then CheckoutConfig.settings.alertBlinkCount else 0)


# Display safe alert warning message.
#
# @param message [String] Message to display.
# @param blink [Boolean, optional] If true (default), container is blinked.
@safeWarning = (message, blink=false) ->
  safeDisplay(CheckoutConfig.uiRef.warningText, message, if blink then 1 else 0)


# Display the alert message.
#
# @param textRef [jQuery] Div reference for the message.
# @param message [String] The message.
# @param blinkCount [Integer, optional] Number of blinks, if any.
safeDisplay = (textRef, message, blinkCount=0) ->
  body = CheckoutConfig.uiRef.container
  text = textRef
  cls = "alert-blink"

  text.text(message)
  text.removeClass("alert-off")
  return unless blinkCount > 0

  body.addClass(cls)
  blinksToGo = blinkCount * 2  # *2 because every other step is a blink removal step.
  timeout = 150
  stillBlinking = true

  timeCb = () ->
    body.toggleClass(cls)
    if --blinksToGo > 0
      setTimeout(timeCb, timeout)
    else
      stillBlinking = false
      body.removeClass(cls)
  setTimeout(timeCb, timeout)

# Remove safe alert message, if the alert has been completed.
@safeAlertOff = ->
  return if stillBlinking

  CheckoutConfig.uiRef.errorText.addClass("alert-off")
  CheckoutConfig.uiRef.warningText.addClass("alert-off")
  return


class @RefreshButton
  constructor: (func, title=gettext("Refresh")) ->
    @refresh = func
    @title = title

  render: ->
    $('<button class="btn btn-default hidden-print">').append(
      $('<span class="glyphicon glyphicon-refresh">')
    ).on(
      "click", @refresh
    ).attr(
      "title", @title
    )


@addEnableCheck = () ->
  $(".check_enabled a").each((index, element) ->
    # Replace href of the 'a' element with dummy.
    target = element.href
    element.href = "javascript:void(0)"

    # Add click script that ensures the element or its parent is not disabled when 'a' is clicked.
    $(element).on("click", (event) ->
      if not ($(event.target).hasClass("disabled") and $(event.target.parentElement).hasClass("disabled"))
        # Not disabled, change location.
        window.location = target
    )
  )

