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
                <label for="item-edit-price-input"
                       class="col-sm-2 control-label">
                  Price
                </label>
                <div class="col-sm-4">
                  <div class="input-group">
                    <input id="item-edit-price-input"
                           type="number"
                           step="any"
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
        <div class="modal-footer">
          <button class="btn btn-default"
                  data-dismiss="modal">
            Cancel
          </button>
          <button id="item-edit-save-button"
                  class="btn btn-primary">
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
    @saveButton = dialog.find('#item-edit-save-button')

    dialog.find('#item-edit-vendor-info').append(
      new VendorInfo(item.vendor, title=false).render()
    )

    @typeInput.append(
      for t in ItemSearchForm.itemtypes
        $('<option>').attr('value', t.name).text(t.description)
    )
    @stateInput.append(
      for s in ItemSearchForm.itemstates
        $('<option>').attr('value', s.name).text(s.description)
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

    @saveButton.click(@onSave)
    dialog.on('hidden.bs.modal', -> do dialog.remove)
    @dialog = dialog

  show: => @dialog.modal()

  onSave: => @action(do @getFormState)

  getFormState: =>
    code: @item.code

    name: @nameInput.val()
    price: @priceInput.val() * 100
    itemtype: @typeInput.val()
    state: @stateInput.val()
    abandoned: @abandonedYes.prop('checked')
