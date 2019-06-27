class Config
  uiId:
    container: null
    body: null
    errorText: null
    warningText: null
    glyph: null
    stateText: null
    subtitleText: null
    codeInput: null
    codeForm: null
    codeFormMessage: null
    modeMenu: null
    overseerLink: null
    statsLink: null
    languageSelection: null
    dialog: null
    printButton: null
  uiRef:
    container: null
    body: null
    errorText: null
    glyph: null
    stateText: null
    subtitleText: null
    codeInput: null
    codeForm: null
    codeFormMessage: ""  # optional ref.
    modeMenu: null
    overseerLink: null
    statsLink: null
    languageSelection: ""  # optional ref.
    dialog: null
    printButton: null
  settings:
    itemPrefix: null
    counterPrefix: ":*"
    removeItemPrefix: "-"
    payPrefix: "+"
    quickPayExtra: ""
    counterCode: null
    clerkName: null
    alertBlinkCount: 4
    purchaseMax: 400

  # Check existence of uiId values and bind their references to uiRef.
  # @return True if errors. False if all ok.
  check: ->
    errors = false
    for key, value of @uiId
      element = $("#" + value)
      unless element? and element.length == 1
        if not @uiRef[key]?
          console.error("Name #{value} does not identify an element for #{key}.")
          errors = true
        else
          @uiRef[key] = $()  # mark optionals as empty.
        continue
      @uiRef[key] = element
    return errors

window.CheckoutConfig = new Config()

#region Cents conversion functions

# Length of digits in fraction part. Leave as 2 for cents representation.
Number.FRACTION_LEN = 2

# Magnitude of fraction part. Automatically calculated. (100 if FRACTION_LEN is 2.)
Number.FRACTION = 10 ** Number.FRACTION_LEN

# Format the fixed number contained to a "price".
# @return [String] Formatted price.
# @note This does not work correctly for floating point numbers.
Number.prototype.formatCents = () ->
  # Separate wholes and fractions from the cents.
  wholes = Math.floor(Math.abs(this / Number.FRACTION))
  fraction = Math.abs(this % Number.FRACTION)

  # Add prefix-zeros to the fraction part, so 2 becomes ".02" and 20 becomes ".20".
  fraction_str = ""
  fraction_len = ("" + fraction).length
  for ignored in [fraction_len...Number.FRACTION_LEN]
    fraction_str += "0"

  # Add the actual fraction after the prefix-zeros.
  fraction_str += fraction

  # Adjust sign and create output.
  if this < 0 then wholes = "-" + wholes
  return wholes + "." + fraction_str

# Parse "price" tag to cents, ie. integer.
# @return [Number] Parsed integer or null on error.
String.prototype.parseCents = () ->
  # Match the string to parts: sign, wholes, fraction
  pat = /^(-?)(\d*)(?:[,.](\d*))?$/
  matcher = pat.exec(this)
  if not matcher? then return null

  # Ensure that values are defined.
  matcher[1] = "" unless matcher[1]?
  matcher[2] = "0" unless matcher[2]?
  matcher[3] = "0" unless matcher[3]?

  # Convert to integer.
  wholes = matcher[2] - 0
  fraction = matcher[3] - 0

  # Adjust fraction so that ".2" equals 20 and ".02" equals 2.
  fraction_exp = 10 ** (Number.FRACTION_LEN - matcher[3].length)
  fraction = Math.round(fraction * fraction_exp)

  # 100 cents per a whole. (or whatever the FRACTION has been defined)
  cents = wholes * Number.FRACTION

  # Adjust by sign, and add the fraction part to cents.
  if matcher[1] != "-"
    cents += fraction
  else
    cents = -cents - fraction

  return cents

#endregion
