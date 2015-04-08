class @ItemSearchForm

  @itemtypes = []
  @itemstates = []

  constructor: (action) ->
    @action = action

    @searchInput = $('<input type="text" id="item_search_input" class="form-control">')
    @searchCodeInput = $('<input type="text" id="item_code_search_input" class="form-control">')
    @searchVendorInput = $('<input type="number" step="any" min="1" id="vendor_search_input" class="form-control">')
    @minPriceInput = $('<input type="number" step="any" min="0" id="item_search_min_price" class="form-control">')
    @maxPriceInput = $('<input type="number" step="any" min="0" id="item_search_max_price" class="form-control">')
    @typeInput = $('<select multiple class="form-control" id="item_search_type">').append(
      $('<option>').attr('value', t.name).text(t.description) for t in ItemSearchForm.itemtypes
    )
    @stateInput = $('<select multiple class="form-control" id="item_search_state">').append(
      $('<option>').attr('value', s.name).text(s.description) for s in ItemSearchForm.itemstates
    )

    @form = $('<form role="form" class="form-horizontal">').append([
      $('<div class="form-group">').append([
        $('<label for="item_search_input" class="control-label col-sm-2">Name</label>')
        $('<div class="input-group col-sm-10">').append(@searchInput)
      ])
      $('<div class="form-group">').append([
        $('<label for="item_code_search_input" class="control-label col-sm-2">Bar code</label>')
        $('<div class="input-group col-sm-10">').append(@searchCodeInput)
      ])
      $('<div class="form-group">').append([
        $('<label for="vendor_search_input" class="control-label col-sm-2">Vendor ID</label>')
        $('<div class="input-group col-sm-2">').append(@searchVendorInput)
      ])
      $('<div class="form-group">').append([
        $('<label for="item_search_min_price" class="control-label col-sm-2">Minimum price</label>')
        $('<div class="input-group col-sm-2">').append([
          @minPriceInput
          $('<span class="input-group-addon">').text('€')
        ])
      ])
      $('<div class="form-group">').append([
        $('<label for="item_search_max_price" class="control-label col-sm-2">Maximum price</label>')
        $('<div class="input-group col-sm-2">').append([
          @maxPriceInput
          $('<span class="input-group-addon">').text('€')
        ])
      ])
      $('<div class="form-group">').append([
        $('<label for="item_search_type" class="control-label col-sm-2">Type</label>')
        $('<div class="input-group col-sm-10">').append(@typeInput)
      ])
      $('<div class="form-group">').append([
        $('<label for="item_search_state" class="control-label col-sm-2">State</label>')
        $('<div class="input-group col-sm-10">').append(@stateInput)
      ])
      $('<div class="col-sm-offset-2">').append(
        $('<button type="submit" class="btn btn-default" class="col-sm-1">')
          .text('Search')
      )
    ])
    @form.off('submit')
    @form.submit(@onSubmit)

  render: -> @form

  onSubmit: (event) =>
    do event.preventDefault
    @action(
      @searchInput.val()
      @searchCodeInput.val()
      @searchVendorInput.val()
      @minPriceInput.val()
      @maxPriceInput.val()
      @typeInput.val()
      @stateInput.val()
    )
