@graphLoader = (url, instance) ->
  req = new XMLHttpRequest()

  instance.rawData_ = []
  last_update = new Date().getTime()
  last_size = 0

  req.onreadystatechange = () ->
    if req.readyState == 4
      if req.status == 200 ||  # Normal http
          req.status == 0      # Chrome w/ --allow-file-access-from-files
        instance.loadedEvent_(req.responseText)
    else if req.readyState == 3
      # If the download is not done yet, process whatever we have and
      # update the graph.
      now = new Date().getTime()
      if now - last_update > 1000 / 25
        new_str = req.responseText.slice(last_size)
        last_size = req.responseText.length
        new_data = instance.parseCSV_(new_str)
        instance.rawData_.push.apply(instance.rawData_, new_data)
        instance.cascadeDataDidUpdateEvent_()
        instance.predraw_()
        last_update = new Date().getTime()

  req.open("GET", url, true)
  req.send(null)
  return
