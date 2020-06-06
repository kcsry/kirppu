class @ItemEditDialog

  @priceTagCss = []

  constructor: (item, action) ->
    @item = item
    @action = action

    dialog = $(Template.item_edit_dialog(
      CURRENCY: CURRENCY.raw
      item_types: ItemSearchForm.itemtypes
      item_states: ItemSearchForm.itemstates
    ))

    @typeInput = dialog.find('#item-edit-type-input')
    @stateInput = dialog.find('#item-edit-state-input')
    @nameInput = dialog.find('#item-edit-name-input')
    @codeInput = dialog.find('#item-edit-code-input')
    @priceInput = dialog.find('#item-edit-price-input')
    @abandonedYes = dialog.find('#item-edit-abandoned-yes')
    @abandonedNo = dialog.find('#item-edit-abandoned-no')
    @priceConfirm = dialog.find('#item-edit-price-confirm')
    @errorDiv = dialog.find('#item-edit-error')
    @saveButton = dialog.find('#item-edit-save-button')
    @printButton = dialog.find('#item-edit-print-button')

    @priceConfirm.change(=>
      if @priceConfirm.prop('checked')
        @priceInput.prop('readonly', false)
      else
        @priceInput.val(@item.price.formatCents())
        @priceInput.prop('readonly', true)
    )

    dialog.find('input').change(@onChange).on("keyup", @onChange)
    dialog.find('select').change(@onChange)
    dialog.on('hidden.bs.modal', -> do dialog.remove)
    dialog.on('shown.bs.modal', => do @onShown)
    @dialog = dialog

    @priceTag = $('.item_template').clone()
      .removeClass('item_template')
      .addClass('item_short')

    @saveButton.click(@onSave)
    @printButton.click(@onPrint)

    @setItem(item)

  setItem: (item) =>
    @item = item

    do @updatePriceTag

    @dialog.find('#item-edit-vendor-info').empty().append(
      Template.vendor_info(vendor: item.vendor, title: false)
    )
    @nameInput.val(item.name)
    @codeInput.val(item.code)
    @priceInput.val(item.price.formatCents())
    @typeInput.val(item.itemtype)
    @stateInput.val(item.state)
    if item.abandoned
      @abandonedYes.prop('checked', true)
    else
      @abandonedNo.prop('checked', true)

    @priceConfirm.prop('checked', false)
    @priceConfirm.change()
    @saveButton.prop('disabled', true)
    return

  updatePriceTag: =>
    item = @item
    tag = @priceTag
    tag.find('.item_name').text(item.name)
    tag.find('.item_price').text(item.price.formatCents())
    tag.find('.item_head_price').text(item.price.formatCents())
    tag.find('.item_adult_tag').text(if item.adult then 'K-18' else '')
    tag.find('.item_vendor_id').text(item.vendor.id)
    tag.find('.item_extra_code').text(item.code)
    Api.get_barcodes(codes: JSON.stringify(item.code)).done((codes) ->
      tag.find('.barcode_container > img').attr('src', codes[0])
    )

  show: => do @dialog.modal

  hide: => @dialog.modal('hide')

  onShown: =>
    doc = window.frames['item-edit-print-frame'].document
    $(doc.head).append(
      for css in ItemEditDialog.priceTagCss
        $('<link>').attr({rel: 'stylesheet', 'href': css})
    )
    console.log(ItemEditDialog.priceTagCss)
    $(doc.body).find('#items').empty().append(@priceTag)

  displayError: (msg) =>
    if msg?
      @errorDiv.text(msg)
      @errorDiv.removeClass('alert-off')
    else
      @errorDiv.text('')
      @errorDiv.addClass('alert-off')

  onChange: =>
    # Enable or disable save button depending on wheter any values have
    # been changed.
    if do @hasChanged
      @saveButton.prop('disabled', false)
    else
      @saveButton.prop('disabled', true)
    return

  hasChanged: =>
    state = do @getFormState
    if state.price == ""
      # Not-a-number, detected by browser.
      @priceInput.parent().addClass("has-error")
      return false
    @priceInput.parent().removeClass("has-error")
    if Math.round((state.price - 0) * 100) != @item.price
      return true
    for attr in ['name', 'itemtype', 'state', 'abandoned']
      if state[attr] != @item[attr]
        return true
    return false

  onSave: =>
    @displayError(null)
    @action(do @getFormState, @)

  onPrint: =>
    frame = window.frames['item-edit-print-frame']
    do frame.window.focus
    do frame.window.print

  getFormState: =>
    code: @item.code

    name: @nameInput.val()
    price: @priceInput.val()
    itemtype: @typeInput.val()
    state: @stateInput.val()
    abandoned: @abandonedYes.prop('checked')
