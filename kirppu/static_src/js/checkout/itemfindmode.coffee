class @ItemFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("item_find", @)

  constructor: ->
    super
    @itemList = new ItemFindList()
    @searchForm = new ItemSearchForm(@doSearch)
    @search = null

  enter: ->
    super
    @cfg.uiRef.body.empty()
    @cfg.uiRef.body.append(@searchForm.render())
    @cfg.uiRef.body.append(@itemList.render())

  glyph: -> "search"
  title: -> "Item Search"

  doSearch: (query, code, vendor, min_price, max_price, type, state) =>
    @search =
      query: query
      code: code
      vendor: vendor
      min_price: min_price
      max_price: max_price
      item_type: if type? then type.join(' ') else ''
      item_state: if state? then state.join(' ') else ''
    Api.item_search(@search).done(@onItemsFound)

  onItemsFound: (items) =>
    @itemList.body.empty()
    for item_, index_ in items
      ((item, index) =>
        @itemList.append(
          item,
          index + 1,
          @onItemClick,
        )
      )(item_, index_)

  onItemClick: (item) =>
    do new ItemEditDialog(item, @onItemSaved).show

  onItemSaved: (item, dialog) =>
    Api.item_edit(item).done((editedItem) =>
      dialog.setItem(editedItem)
      if @search?
        Api.item_search(@search).done(@onItemsFound)
    ).fail((jqXHR) =>
      msg = "Item edit failed (#{jqXHR.status}): #{jqXHR.responseText}"
      dialog.displayError(msg)
    )
