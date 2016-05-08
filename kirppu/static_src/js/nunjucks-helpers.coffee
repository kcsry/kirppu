YES_NO_INDICES =
  "true": 0,
  "false": 1,
  "null": 3,
  "undefined": 3

# yesno-helper like one found in django templates.
yesnoHelper = (bValue, choices) ->
  if typeof(choices) != "string"
    choices = "yes,no"
  choices = choices.split(",")
  if !(2 <= choices.length <= 3)
    console.error("Choices must contain either two or three words separated by comma!")
    return null

  sValue = "" + bValue
  if not (sValue of YES_NO_INDICES)
    console.warn("Value not found in lookup table: " + sValue)
    sValue = "undefined"
  return choices[Math.min(YES_NO_INDICES[sValue], choices.length - 1)]

dateTime = (value) ->
  return DateTimeFormatter.datetime(value)


class @Templates
  @render: (name, context={}) ->
    Templates._configure()
    return nunjucks.render(name, context)

  @_env = null

  # Lazy initialization of nunjucks environment.
  # The Environment initialization "needs" the templates to exist before it is created for it to
  # actually load the precompiled ones.
  @_configure: ->
    unless Templates._env
      env = Templates._env = nunjucks.configure()
      env.addFilter("displayPrice", displayPrice)
      env.addFilter("yesno", yesnoHelper)
      env.addFilter("dateTime", dateTime)
    return Templates._env
