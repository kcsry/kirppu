# Base class for modes where the receipt is a list of items.
#
# @abstract
class @ItemCheckoutMode extends CheckoutMode

  constructor: ->
    super
    @receipt = new ItemReceiptTable()

  enter: ->
    super
    @cfg.uiRef.body.append(@receipt.render())

  # Create a row in receipt table.
  # All arguments are used for display-only.
  #
  # @param index [Integer] Index of the item.
  # @param code [String] Item code.
  # @param name [String] Item name.
  # @param price [Integer, optional] Price of the item in cents.
  # @param rounded [Boolean, optional] Should the price be displayed also as rounded?
  # @return [$] Table row (tr element) as jQuery object.
  createRow: (index, code, name, price=null, rounded=false) ->
    return @receipt.createRow(index, code, name, price, rounded)
