
populateChart = (chart, api_func) ->
  appendToChart = (responseJSON) ->
    brought_data = ([new Date(p[0]), p[1], p[2], p[3], p[4], p[5]] for p in responseJSON when p)
    chart.updateOptions('file': brought_data)

  onError = (jqXHR) ->
    safeAlert("Fetching chart data failed.")

  api_func().done(appendToChart).fail(onError)

window.populateChart = populateChart
