class LostAndFound extends CheckoutMode
  ModeSwitcher.registerEntryPoint("lost_and_found", @)

  title: -> gettext("Lost and found properties")
  glyph: -> "sunglasses"
  inputPlaceholder: -> gettext("Barcode of Item to mark as Lost Property")

  constructor: (args...) ->
    super(args...)
    @table = Template.lost_and_found_table()
    @list = $(@table.querySelector("tbody"))

  enter: ->
    super
    @cfg.uiRef.codeForm.removeClass("hidden")
    @cfg.uiRef.body.append(@table)

  exit: ->
    @cfg.uiRef.codeForm.addClass("hidden")
    super

  actions: -> [
    ["", (code) => Api.item_mark_lost(code: code).then(@onMarked, @onResultError)]
  ]

  onMarked: (item) =>
    @list.append(Template.lost_and_found_table_item(item: item))

  onResultError: (jqXHR) =>
    if jqXHR.status == 404
      safeAlert(gettext("No such item"))
      return
    safeAlert("Error:" + jqXHR.responseText)
    return

