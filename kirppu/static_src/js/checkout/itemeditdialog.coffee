class @ItemEditDialog

  html: '''
  <div class="modal fade">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <button class="close"
                  data-dismiss="modal"
                  aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
          <h4 class="modal-title">Edit Item</h4>
        </div>
        <div class="modal-body">
          <div class="container-fluid">
            <form class="form-horizontal">
              <div class="form-group">
                <label for="item-edit-name-input"
                       class="col-sm-2 control-label">
                  Name
                </label>
                <div class="col-sm-10">
                  <input id="item-edit-name-input"
                         type="text"
                         class="form-control"
                         readonly/>
                </div>
              </div>
              <div class="form-group">
                <label for="item-edit-code-input"
                       class="col-sm-2 control-label">
                  Code
                </label>
                <div class="col-sm-3">
                  <input id="item-edit-code-input"
                         type="text"
                         class="form-control receipt-code"
                         readonly/>
                </div>
              </div>
              <div class="form-group">
                <label class="col-sm-2 control-label">Vendor</label>
                <div id="item-edit-vendor-info" class="col-sm-10"></div>
              </div>
              <div class="form-group">
                <div class="col-sm-10 col-sm-offset-2">
                  <div class="checkbox">
                    <label for="item-edit-price-confirm">
                      <input id="item-edit-price-confirm"
                             type="checkbox"/>
                      Vendor has requested a price change.
                    </label>
                  </div>
                </div>
              </div>
              <div class="form-group">
                <label for="item-edit-price-input"
                       class="col-sm-2 control-label">
                  Price
                </label>
                <div class="col-sm-4">
                  <div class="input-group">
                    <input id="item-edit-price-input"
                           type="number"
                           step="0.50"
                           min="0"
                           class="form-control"
                           readonly/>
                    <span class="input-group-addon">&euro;</span>
                  </div>
                </div>
              </div>
              <div class="form-group">
                <label for="item-edit-type-input"
                       class="col-sm-2 control-label">
                  Type
                </label>
                <div class="col-sm-10">
                  <select id="item-edit-type-input"
                          class="form-control"
                          disabled/>
                </div>
              </div>
              <div class="form-group">
                <label for="item-edit-state-input"
                       class="col-sm-2 control-label">
                  State
                </label>
                <div class="col-sm-10">
                  <select id="item-edit-state-input"
                          class="form-control"
                          disabled/>
                </div>
              </div>
              <div class="form-group">
                <label for="item-edit-abandoned-input"
                       class="col-sm-2 control-label">
                  Abandoned
                </label>
                <div class="col-sm-10">
                  <label for="item-edit-abandoned-yes"
                         class="radio-inline">
                    <input id="item-edit-abandoned-yes"
                           name="item-edit-abandoned-input"
                           type="radio"
                           value="true"
                           disabled/>
                      Yes
                  </label>
                  <label for="item-edit-abandoned-no"
                         class="radio-inline">
                    <input id="item-edit-abandoned-no"
                           name="item-edit-abandoned-input"
                           type="radio"
                           value="false"
                           disabled/>
                      No
                  </label>
                </div>
              </div>
            </form>
          </div>
        </div>
        <div id="item-edit-error"
             role="alert"
             class="alert alert-danger alert-off"></div>
        <div class="modal-footer">
          <button class="btn btn-default"
                  data-dismiss="modal">
            Cancel
          </button>
          <button id="item-edit-save-button"
                  class="btn btn-primary"
                  disabled>
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
  '''

  constructor: (item, action) ->
    @item = item
    @action = action

    dialog = $(@html)

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

    @typeInput.append(
      for t in ItemSearchForm.itemtypes
        $('<option>').attr('value', t.name).text(t.description)
    )
    @stateInput.append(
      for s in ItemSearchForm.itemstates
        $('<option>').attr('value', s.name).text(s.description)
    )

    @priceConfirm.change(=>
      if @priceConfirm.prop('checked')
        @priceInput.prop('readonly', false)
      else
        @priceInput.val(@item.price / 100)
        @priceInput.prop('readonly', true)
    )

    dialog.find('input').change(@onChange)
    dialog.find('select').change(@onChange)

    @saveButton.click(@onSave)
    dialog.on('hidden.bs.modal', -> do dialog.remove)
    @dialog = dialog

    @setItem(item)

  setItem: (item) =>
    @item = item

    @dialog.find('#item-edit-vendor-info').empty().append(
      new VendorInfo(item.vendor, title=false).render()
    )
    @nameInput.val(item.name)
    @codeInput.val(item.code)
    @priceInput.val(item.price / 100)
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

  show: => @dialog.modal()

  hide: => @dialog.modal('hide')

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
    if state.price * 100 != @item.price
      return true
    for attr in ['name', 'itemtype', 'state', 'abandoned']
      if state[attr] != @item[attr]
        return true
    return false

  onSave: =>
    @displayError(null)
    @action(do @getFormState, @)

  getFormState: =>
    code: @item.code

    name: @nameInput.val()
    price: @priceInput.val()
    itemtype: @typeInput.val()
    state: @stateInput.val()
    abandoned: @abandonedYes.prop('checked')
