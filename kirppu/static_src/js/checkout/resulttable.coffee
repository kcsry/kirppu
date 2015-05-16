class @ResultTable
  constructor: (caption) ->
    @dom = $('<table class="table table-striped table-hover table-condensed">')
    if caption? then @dom.append($('<caption class="h3">').text(caption))
    @head = $('<tr>')
    @body = $('<tbody>')
    @dom.append($('<thead>').append(@head), @body)

  render: -> @dom

  # List of column classes.
  columns: []

  # Generate row of columns, as defined by columns, filled with texts.
  #
  # @param element [String] DOM Element to generate.
  # @param texts [Array] Texts to put in cells, one element per column.
  # @param only_first_class [optional, Boolean] If true, only first class of column classes is added to cell.
  # @return [Array] List of jQuery elements ready for adding into tr element.
  generate: (element, texts, only_first_class=false) ->
    result = []
    for i in [0...@columns.length]
      column_class = @columns[i]
      text = texts[i] ? ""

      if only_first_class
        column_class = column_class.replace(new RegExp(" .*"), "")
      query = "<#{ element }>"
      e = $(query)
      column_class = column_class.trim()
      if column_class.length > 0
        e.addClass(column_class)
      result.push(e.text(text))
    return result
