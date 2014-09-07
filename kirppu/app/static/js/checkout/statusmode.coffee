class @StatusMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("status_mode", @)

  title: -> "Status Mode"

  constructor: ->
    super

  enter: ->
    super

    canvas = $('<div id="flots_canvas" style="width: 600px; height: 300px"">')
    @cfg.uiRef.body.append(canvas)

    Api.get_stats().done(@onGotStats)

  onGotStats: (stats) =>
    euroFormatter = (v, axis) ->
      v.toFixed(axis.tickDecimals) + "€";

    $.plot(
      "#flots_canvas",
      [
        { data: stats['unsold'], label: 'Unsold' }
        { data: stats['money'], label: 'Money' }
      ],
      {
        series: { lines: { show: true }, points: { show: true } }
        xaxis: { mode: "time" },
        yaxis: { tickFormatter: euroFormatter }
      }
    )

